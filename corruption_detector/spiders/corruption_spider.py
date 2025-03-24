import scrapy
from scrapy_playwright.page import PageMethod
from textblob import TextBlob
from corruption_detector.items import CorruptionItem

# Importamos las funciones de extracción para cada fuente
from corruption_detector.sources import elConfidencial, rtve, veinteMinutos

class MultiSourceSpider(scrapy.Spider):
    name = "multisource_spider"
    allowed_domains = ["elconfidencial.com", "rtve.es", "20minutos.es"]
    
    # URLs de inicio que se visitarán
    start_urls = [
        "https://www.elconfidencial.com/espana/",
        "https://www.rtve.es/noticias/",
        "https://www.20minutos.es/"
    ]
    
    # Palabras clave relacionadas con corrupción
    corruption_keywords = [
        "corrupción", "fraude", "malversación", "soborno",
        "tráfico de influencias", "enriquecimiento ilícito",
        "blanqueo de capitales", "prevaricación", "cohecho", "financiación ilegal"
    ]
    
    def start_requests(self):
        """
        Personaliza las peticiones iniciales añadiendo la configuración de Playwright.
        """
        for url in self.start_urls:
            domain = url.split("/")[2]
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_selector", "article.cell", timeout=60000)
                    ],
                    "source": domain
                },
                callback=self.parse_source
            )
    
    async def parse_source(self, response):
        """
        Extrae enlaces a artículos usando el extractor correspondiente según el dominio
        y genera peticiones a parse_article.
        """
        page = response.meta.get("playwright_page")
        if page:
            html = await page.content()
            await page.close()
        else:
            html = response.text
        
        selector = scrapy.Selector(text=html)
        domain = response.meta.get("source", "")
        self.logger.info(f"Procesando dominio: {domain}")
        
        # Diccionario que relaciona cada dominio con su función extractor
        extractors = {
            "elconfidencial.com": elConfidencial.extract_article_links,
            "rtve.es": rtve.extract_article_links,
            "20minutos.es": veinteMinutos.extract_article_links,
        }
        extractor = next((fn for key, fn in extractors.items() if key in domain), None)
        if extractor is None:
            self.logger.warning(f"No se encontró extractor para el dominio: {domain}")
            return
        
        articles = extractor(selector)
        self.logger.info(f"Número de artículos encontrados en {domain}: {len(articles)}")
        for title, link in articles:
            full_link = response.urljoin(link)
            self.logger.info(f"Artículo encontrado en {domain}: Título='{title}', Enlace='{full_link}'")
            meta = {"source": domain, "playwright": True, "playwright_include_page": True}
            if "rtve.es" in domain:
                meta["article_title"] = title  # Se guarda el título para RTVE
            yield response.follow(
                full_link,
                callback=self.parse_article,
                meta=meta
            )
    
    async def parse_article(self, response):
        """
        Extrae el contenido del artículo, evalúa keywords y sentimiento,
        y genera un CorruptionItem si se superan ciertos umbrales.
        """
        source = response.meta.get("source", "")
        page = response.meta.get("playwright_page")
        if page:
            if "elconfidencial.com" in source:
                container_selector = "div.article-body, div.article-content, div.news-body"
            elif "rtve.es" in source:
                container_selector = "div.content-body"
            elif "20minutos.es" in source:
                container_selector = "div.article-body, div.article-content"
            else:
                container_selector = "body"
            
            try:
                await page.wait_for_selector(container_selector, timeout=30000)
            except Exception as e:
                self.logger.error(f"Error esperando contenedor en {source}: {e}")
            
            html = await page.content()
            await page.close()
        else:
            html = response.text
        
        selector = scrapy.Selector(text=html)
        if "elconfidencial.com" in source:
            title, paragraphs = elConfidencial.extract_article_content(selector)
        elif "rtve.es" in source:
            title, paragraphs = rtve.extract_article_content(selector, response.meta)
        elif "20minutos.es" in source:
            title, paragraphs = veinteMinutos.extract_article_content(selector)
        else:
            title, paragraphs = "", []
        
        content = " ".join(p.strip() for p in paragraphs if p.strip())
        self.logger.info(f"Contenido del artículo en {source}: {content[:500]}...")
        
        preview = ""
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            preview += (" " if preview else "") + p
            if len(preview) >= 800:
                break
        if len(preview) > 800:
            preview = preview[:800] + "..."
        elif not preview:
            preview = content[:800] + "..." if len(content) > 800 else content
        
        combined_text = f"{title}"
        keyword_matches = [
            kw for kw in self.corruption_keywords
            if kw.lower() in combined_text.lower() or kw.lower() in content.lower()
        ]
        self.logger.info(f"Keywords encontradas en {source}: {keyword_matches}")
        
        blob = TextBlob(content)
        self.logger.info(f"Polaridad del sentimiento en {source}: {blob.polarity}")
        
        risk_score = sum(
            10 if kw in ["fraude", "malversación", "blanqueo de capitales"] else 5
            for kw in keyword_matches
        )
        if blob.polarity < -0.4:
            risk_score += 7
        self.logger.info(f"Puntaje de riesgo en {source}: {risk_score}")
        
        if risk_score >= 3:
            alert_level = (
                "CRÍTICA" if any(kw in title.lower() for kw in ["fraude", "malversación", "blanqueo de capitales"])
                else "ALTA" if risk_score > 15 else "MEDIA"
            )
            yield CorruptionItem(
                title=title,
                link=response.url,
                content_preview=preview,
                keywords_found=keyword_matches,
                sentiment_polarity=round(blob.polarity, 2),
                risk_score=risk_score,
                alert_level=alert_level
            )
