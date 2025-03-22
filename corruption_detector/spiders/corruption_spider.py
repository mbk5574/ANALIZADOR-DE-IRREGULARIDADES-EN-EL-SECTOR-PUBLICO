import scrapy
from scrapy_playwright.page import PageMethod
from textblob import TextBlob
from corruption_detector.items import CorruptionItem

class MultiSourceSpider(scrapy.Spider):
    name = "multisource_spider"
    allowed_domains = ["elconfidencial.com", "rtve.es", "20minutos.es"]

    #URLs de inicio que el spider visitara primero antes de ir navegando los articulos con mayor score para extraer su contenido
    start_urls = [
        "https://www.elconfidencial.com/espana/",
        "https://www.rtve.es/noticias/",
        "https://www.20minutos.es/"
    ]

    #palabras clave mas interesantes para el tema que estamos tratando (REVISAR SI HABRIA ALGUNA MAS O ESTO YA ESTA BIEN)
    corruption_keywords = [
        "corrupción", "fraude", "malversación", "soborno",
        "tráfico de influencias", "enriquecimiento ilícito",
        "blanqueo de capitales", "prevaricación", "cohecho", "financiación ilegal"
    ]

    def start_requests(self):
        """
        Sobrescribimos start_requests() para personalizar como se construyen
        las peticiones. Se aniade la configuracion de Playwright en meta.
        """
        for url in self.start_urls:
            #extraemos el dominio de la URL para usarlo luego en parse_source
            domain = url.split("/")[2]
            #generamos la Request (Scrapy) indicando que use Playwright
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,     #activamos Playwright
                    "playwright_include_page": True,  
                    "playwright_page_methods": [
                        #Esperamos que la pagina termine de cargar
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_selector", "article.cell", timeout=60000)
                    ],
                    "source": domain
                },
                callback=self.parse_source
            )

    async def parse_source(self, response):
        """
        parse_source se encarga de extraer enlaces a articulos en cada pagina fuente
        (El Confidencial, RTVE y 20minutos en este caso) y luego llama a parse_article para analizar su contenido.
        """
        #obtenemos la pagina de Playwright (si existe)
        page = response.meta.get("playwright_page")
        if page:
            html = await page.content()             #obtenemos el HTML completo tras la renderizacion
            await page.close()             #cerramos la pagina de Playwright
        else:
            html = response.text #si no tuvieramos Playwright, usariamos el HTML sin renderizar

        #creamos un Selector de Scrapy a partir del HTML
        selector = scrapy.Selector(text=html)
        #obtenemos el dominio guardado en meta
        domain = response.meta.get("source", "")
        self.logger.info(f"Procesando dominio: {domain}")

        #segun el dominio, utilizamos selectores distintos para encontrar los articulos
        if "elconfidencial.com" in domain:
            #El Confidencial: puede usar <article>, <div class="article-item">, <div class="news-card">
            articles = selector.css("article, div.article-item, div.news-card")
            for article in articles:
                title = article.css("h2::text, h3::text").get(default="").strip()
                link = article.css("a::attr(href)").get()
                if title and link:
                    #generamos la URL absoluta
                    full_link = response.urljoin(link)
                    self.logger.info(f"Artículo encontrado en {domain}: Título='{title}', Enlace='{full_link}'")
                    #hacemos request a cada articulo para analizarlo en parse_article
                    yield response.follow(
                        full_link,
                        callback=self.parse_article,
                        meta={
                            "source": domain,
                            "playwright": True,
                            "playwright_include_page": True,
                        }
                    )
        elif "rtve.es" in domain:
            articles = selector.css("article.cell")
            for article in articles:
                title = article.css("h3 a span.maintitle::text").get(default="").strip() 
                link = article.css("h3 a::attr(href)").get()
                if title and link:
                    full_link = response.urljoin(link)
                    self.logger.info(f"Artículo encontrado en {domain}: Título='{title}', Enlace='{full_link}'")
                    yield response.follow(
                        full_link,
                        callback=self.parse_article,
                        meta={
                            "source": domain,
                            "playwright": True,
                            "playwright_include_page": True,
                            "article_title": title 
                        }
                    )
        elif "20minutos.es" in domain:
            articles = selector.css("article.media, article.media.media-big")
            for article in articles:
                link_element = article.css("h1 a, figure a") 
                link = link_element.css("::attr(href)").get()
                title = link_element.css("::text").get(default="").strip()
                if title and link:
                    full_link = response.urljoin(link)
                    self.logger.info(f"Artículo encontrado en {domain}: Título='{title}', Enlace='{full_link}'")
                    yield response.follow(
                        full_link,
                        callback=self.parse_article,
                        meta={
                            "source": domain,
                            "playwright": True,
                            "playwright_include_page": True
                        }
                    )
            return
        else:
            articles = []

        self.logger.info(f"Número de artículos encontrados en {domain}: {len(articles)}")

        for article in articles:
            if "elconfidencial.com" in domain:
                title = article.css("h2::text, h3::text").get(default="").strip()
                link = article.css("a::attr(href)").get()
            elif "rtve.es" in domain:
                title = article.css("h3 a span.maintitle::text").get(default="").strip()
                link = article.css("h3 a::attr(href)").get() 
            elif "20minutos.es" not in domain: 
                title, link = "", ""

            if title and link:
                full_link = response.urljoin(link)
                self.logger.info(f"Artículo encontrado en {domain}: Título='{title}', Enlace='{full_link}'")
                yield response.follow(
                    full_link,
                    callback=self.parse_article,
                    meta={
                        "source": domain,
                        "playwright": True,
                        "playwright_include_page": True
                    }
                )

    async def parse_article(self, response):
        """
        parse_article recibe la respuesta de cada articulo individual y
        extrae el contenido (parrafos, titulo, etc.), evalua keywords y
        sentimiento, y genera un item si se cumplen los criterios.
        """
        #obtenemos el dominio (fuente) y la pagina de Playwright
        source = response.meta.get("source", "")
        page = response.meta.get("playwright_page")
        if page:
            #dependiendo de la fuente, escogemos un contenedor donde buscar el texto principal u otra ya que tienen distintos htmls
            if "elconfidencial.com" in source:
                container_selector = "div.article-body, div.article-content, div.news-body"
            elif "rtve.es" in source:
                container_selector = "div.content-body"
            elif "20minutos.es" in source:
                container_selector = "div.article-body, div.article-content"
            else:
                container_selector = "body"

            #esperamos a que aparezca ese contenedor en la pagina
            try:
                await page.wait_for_selector(container_selector, timeout=30000)
            except Exception as e:
                self.logger.error(f"Error esperando contenedor en {source}: {e}")
            
            #obtenemos el HTML completo
            html = await page.content()
            await page.close()
        else:
            html = response.text

        #procesamos el HTML con scrapy.Selector
        selector = scrapy.Selector(text=html)

        #extraemos el titulo y los parrafos, segun la estructura de cada medio
        if "elconfidencial.com" in source:
            og_title = selector.css('meta[property="og:title"]::attr(content)').get('')
            meta_description = selector.css('meta[name="description"]::attr(content)').get('')
            title = og_title or selector.css('h1::text').get(default="").strip()
            paragraphs = selector.css('div#news-body-cc p::text').getall()
        elif "rtve.es" in source:
            title = response.meta.get("article_title") 
            paragraphs = selector.css("div.mainContent div.artBody p::text").getall()
        elif "20minutos.es" in source:
            title = selector.css("h1.article-title::text").get(default="").strip()
            paragraphs = selector.css('div.article-body p::text, div.article-content p::text, p.paragraph::text, p.interview-line::text, h2.paragraph-ladillo::text').getall()
        else:
            title, paragraphs = "",

        #unimos todos los parrafos en un solo texto "content"
        content = " ".join(p.strip() for p in paragraphs if p.strip())
        self.logger.info(f"Contenido del artículo en {source}: {content[:500]}...")

        #creamos una vista previa de hasta 800 caracteres
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
        elif not preview:            #si no hay parrafos, ponemos un substring de content o lo que haya
            preview = content[:800] + "..." if len(content) > 800 else content

        #combinamos el título con el contenido para la busqueda de keywords
        combined_text = f"{title}"
        
        #buscamos si alguna palabra clave de "corrupcion" aparece en el titulo o en el cuerpo
        keyword_matches = [
            kw for kw in self.corruption_keywords
            if kw.lower() in combined_text.lower() or kw.lower() in content.lower()
        ]
        self.logger.info(f"Keywords encontradas en {source}: {keyword_matches}")

        #calculamos la polaridad de sentimiento con TextBlob
        blob = TextBlob(content)
        self.logger.info(f"Polaridad del sentimiento en {source}: {blob.polarity}")

        # Calculamos un "risk_score" segun las palabras clave
        # - 10 puntos para "fraude", "malversacion", "blanqueo de capitales"
        # - 5 puntos para las demas
        risk_score = sum(
            10 if kw in ["fraude", "malversación", "blanqueo de capitales"] else 5
            for kw in keyword_matches
        )
        #si la polaridad es muy negativa (< -0.4), sumamos 7 puntos
        if blob.polarity < -0.4:
            risk_score += 7

        self.logger.info(f"Puntaje de riesgo en {source}: {risk_score}")

        #si superamos un umbral de riesgo (>= 3), creamos un CorruptionItem
        if risk_score >= 3:
            #definimos alert_level según si se encuentra una keyword muy grave y segun risk_score
            alert_level = (
                "CRÍTICA" if any(kw in title.lower() for kw in ["fraude", "malversación", "blanqueo de capitales"])
                else "ALTA" if risk_score > 15 else "MEDIA"
            )
            #construimos y devolvemos el item con la informacion relevante
            yield CorruptionItem(
                title=title,
                link=response.url,
                content_preview=preview,
                keywords_found=keyword_matches,
                sentiment_polarity=round(blob.polarity, 2),
                risk_score=risk_score,
                alert_level=alert_level
            )