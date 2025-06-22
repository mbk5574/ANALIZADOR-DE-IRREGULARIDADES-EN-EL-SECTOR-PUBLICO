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
    

    # Se convertirán a minúsculas en __init__
    base_corruption_indicators = [
        "corrupción", "fraude", "malversación", "soborno",
        "tráfico de influencias", "enriquecimiento ilícito",
        "blanqueo de capitales", "prevaricación", "cohecho", "financiación ilegal"
    ]
    
    def __init__(self, *args, **kwargs):
        super(MultiSourceSpider, self).__init__(*args, **kwargs)
        # Recibe los términos del contrato como un string separado por comas
        # Ejemplo de ejecución: scrapy crawl multisource_spider -a contract_terms="Nombre Adjudicatario,Otro Termino"
        contract_terms_input = kwargs.get('contract_terms', '')
        
        if not contract_terms_input:
            self.logger.warning("No se proporcionaron 'contract_terms' específicos del contrato. "
                               "La araña buscará artículos con indicadores de corrupción generales.")
            self.contract_specific_keywords = []
        else:
            # Limpia, convierte a minúsculas y filtra términos vacíos
            self.contract_specific_keywords = [
                term.strip().lower() for term in contract_terms_input.split(',') if term.strip()
            ]
            self.logger.info(f"Términos de búsqueda específicos del contrato inicializados: {self.contract_specific_keywords}")
        
        # Convertir indicadores de corrupción a minúsculas para comparación uniforme
        self.corruption_indicators = [keyword.lower() for keyword in self.base_corruption_indicators]
        self.critical_corruption_terms = [
            kw.lower() for kw in ["fraude", "malversación", "blanqueo de capitales"]
        ]

    def start_requests(self):
        """
        Personaliza las peticiones iniciales añadiendo la configuración de Playwright.
        """
        for url in self.start_urls:
            domain = url.split("/")[2]
            # El selector 'article.cell' es una suposición genérica para las páginas de listado.
            playwright_page_methods = [
                PageMethod("wait_for_load_state", "networkidle"),
                PageMethod("wait_for_selector", "article, .news-item, .articulo", timeout=60000) # Selectores más genéricos
            ]
            # Ejemplo de selector más específico si 'article.cell' es correcto para El Confidencial
            if "elconfidencial.com" in domain:
                 playwright_page_methods = [
                    PageMethod("wait_for_load_state", "networkidle"),
                    PageMethod("wait_for_selector", "article.cell", timeout=60000)
                 ]
            elif "rtve.es" in domain: 
                 playwright_page_methods = [
                    PageMethod("wait_for_load_state", "networkidle"),
                    PageMethod("wait_for_selector", "article.ZEST_ECNMND", timeout=60000) 
                 ]
            elif "20minutos.es" in domain: 
                 playwright_page_methods = [
                    PageMethod("wait_for_load_state", "networkidle"),
                    PageMethod("wait_for_selector", "article.media-object", timeout=60000) 
                 ]


            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": playwright_page_methods,
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
        html = ""
        if page:
            try:
                html = await page.content()
            except Exception as e:
                self.logger.error(f"Error al obtener contenido de la página Playwright para {response.url}: {e}")
                html = response.text 
            finally:
                await page.close()
        else:
            html = response.text
        
        if not html:
            self.logger.warning(f"No se pudo obtener HTML para {response.url}. Omitiendo parse_source.")
            return

        selector = scrapy.Selector(text=html)
        domain = response.meta.get("source", "")
        self.logger.info(f"Procesando dominio: {domain}")
        
        extractors = {
            "elconfidencial.com": elConfidencial.extract_article_links,
            "rtve.es": rtve.extract_article_links,
            "20minutos.es": veinteMinutos.extract_article_links,
        }
        extractor_func = extractors.get(domain)
        
        if extractor_func is None:
            self.logger.warning(f"No se encontró extractor de enlaces para el dominio: {domain}")
            return
            
        articles = extractor_func(selector) 
        self.logger.info(f"Número de artículos potenciales encontrados en {domain}: {len(articles)}")
        
        for title, link in articles:
            if not link: 
                self.logger.warning(f"Enlace vacío o None encontrado en {domain} para el título '{title}'. Omitiendo.")
                continue

            full_link = response.urljoin(link)
            self.logger.info(f"Artículo encontrado en {domain}: Título='{title}', Enlace='{full_link}'")
            
            meta_for_article = {
                "source": domain, 
                "playwright": True, 
                "playwright_include_page": True,
                "original_title_from_source": title 
            }
            if "rtve.es" in domain:
                meta_for_article["article_title"] = title 
            
            yield response.follow(
                full_link,
                callback=self.parse_article,
                meta=meta_for_article
            )
    
    async def parse_article(self, response):
        """
        Extrae el contenido del artículo, evalúa keywords y sentimiento,
        y genera un CorruptionItem si se superan ciertos umbrales.
        """
        source = response.meta.get("source", "")
        page = response.meta.get("playwright_page")
        html = ""

        # Selectores de contenedor de contenido del artículo específicos del sitio
        container_selectors = {
            "elconfidencial.com": "div.article-body, div.article-content, div.news-body",
            "rtve.es": "div.content-body", 
            "20minutos.es": "div.article-body, div.article-content, .article-text" 
        }
        container_selector = container_selectors.get(source, "body") 

        if page:
            try:
                await page.wait_for_selector(container_selector, timeout=30000)
                html = await page.content()
            except Exception as e:
                self.logger.error(f"Error esperando/obteniendo contenido de Playwright para el artículo {response.url} en {source}: {e}")
                html = response.text 
            finally:
                await page.close()
        else:
            html = response.text
        
        if not html:
            self.logger.warning(f"No se pudo obtener HTML para el artículo {response.url}. Omitiendo parse_article.")
            return

        selector = scrapy.Selector(text=html)
        
       
        title_extracted, paragraphs_extracted = "", []
        if "elconfidencial.com" == source:
            title_extracted, paragraphs_extracted = elConfidencial.extract_article_content(selector)
        elif "rtve.es" == source:
          
            title_extracted, paragraphs_extracted = rtve.extract_article_content(selector, response.meta)
        elif "20minutos.es" == source:
            title_extracted, paragraphs_extracted = veinteMinutos.extract_article_content(selector)
        else:
            self.logger.warning(f"No hay extractor de contenido de artículo definido para: {source}")
           
            title_extracted = selector.css('h1::text, h1 *::text').get(default='').strip()
            paragraphs_extracted = selector.css('p::text, p *::text').getall()


        if not title_extracted and response.meta.get("original_title_from_source"):
            title_extracted = response.meta.get("original_title_from_source")
            self.logger.info(f"Usando título de parse_source para {response.url} ya que no se extrajo en parse_article.")
        
        if not title_extracted and not paragraphs_extracted:
            self.logger.warning(f"No se pudo extraer título ni contenido para {response.url} en {source}. Omitiendo artículo.")
            return

      
        title_lower = title_extracted.lower() if title_extracted else ""
        # Unimos parrafos en un solo bloque de texto para el análisis, y luego lo pasamos a minúsculas
        full_content_original = " ".join(p.strip() for p in paragraphs_extracted if p.strip())
        content_lower = full_content_original.lower()

        # --- Lógica de filtrado y keywords ---
        found_contract_terms_in_article = []
        if self.contract_specific_keywords:
            article_is_relevant_to_contract = False
            for term in self.contract_specific_keywords:
                if term in title_lower or term in content_lower:
                    article_is_relevant_to_contract = True
                    found_contract_terms_in_article.append(term)
            
            if not article_is_relevant_to_contract:
                self.logger.debug(f"Artículo en {response.url} no contiene términos específicos del contrato. Omitiendo.")
                return
            self.logger.info(f"Términos del contrato {found_contract_terms_in_article} encontrados en {response.url}")
        
        found_corruption_indicators = [
            kw for kw in self.corruption_indicators
            if kw in title_lower or kw in content_lower
        ]

        if not found_corruption_indicators:
            self.logger.debug(f"Artículo en {response.url} (relevante para contrato o general) no contiene indicadores de corrupción. Omitiendo.")
            return
        self.logger.info(f"Indicadores de corrupción encontrados en {source} ({response.url}): {found_corruption_indicators}")

        # --- Generación de Preview (con texto original) ---
        preview = title_extracted # Empezar preview con el título original
        chars_remaining_for_preview = 800 - len(preview)
        for p_text in paragraphs_extracted:
            if chars_remaining_for_preview <= 0:
                break
            p_clean = p_text.strip()
            if not p_clean: continue
            
            if len(preview) > 0: 
                 preview += " "
                 chars_remaining_for_preview -=1

            if len(p_clean) <= chars_remaining_for_preview:
                preview += p_clean
                chars_remaining_for_preview -= len(p_clean)
            else:
                preview += p_clean[:chars_remaining_for_preview-3] + "..."
                chars_remaining_for_preview = 0
                break
        
        if len(preview) > 800: 
             preview = preview[:797] + "..."
        elif not preview and full_content_original: 
             preview = full_content_original[:797] + "..." if len(full_content_original) > 800 else full_content_original


      
        blob = TextBlob(content_lower) 
        self.logger.info(f"Polaridad del sentimiento en {source} ({response.url}): {blob.polarity}")
        
        risk_score = sum(
            10 if kw in self.critical_corruption_terms else 5
            for kw in found_corruption_indicators
        )
        if blob.polarity < -0.4: # Umbral de sentimiento negativo
            risk_score += 7
        self.logger.info(f"Puntaje de riesgo en {source} ({response.url}): {risk_score}")
        
        # --- Generación del Item ---
        if risk_score >= 3: 
            alert_level = "MEDIA" 
            if any(crit_kw in title_lower for crit_kw in self.critical_corruption_terms if crit_kw in found_corruption_indicators):
                alert_level = "CRÍTICA"
            elif risk_score > 15:
                alert_level = "ALTA"
            
            item = CorruptionItem()
            item['title'] = title_extracted
            item['link'] = response.url
            item['content_preview'] = preview
            item['source'] = source
            item['contract_terms_found'] = found_contract_terms_in_article
            item['corruption_keywords_found'] = found_corruption_indicators
            item['sentiment_polarity'] = round(blob.polarity, 2)
            item['risk_score'] = risk_score
            item['alert_level'] = alert_level
            
            self.logger.info(f"ITEM GENERADO: Alerta {alert_level}, Riesgo {risk_score}, URL: {response.url}")
            yield item
        else:
            self.logger.info(f"Artículo {response.url} no supera umbral de riesgo ({risk_score}). No se genera item.")