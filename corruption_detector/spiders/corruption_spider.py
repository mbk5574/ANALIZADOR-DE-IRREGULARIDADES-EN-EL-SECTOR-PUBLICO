# corruption_detector/spiders/multisource_spider.py

import scrapy
import asyncio
from scrapy_playwright.page import PageMethod
from scrapy.exceptions import CloseSpider
from corruption_detector.items import CorruptionItem
from corruption_detector.sources import elConfidencial, rtve, veinteMinutos, defensa, laRazon, vozPopuli
import unicodedata
import re
from pysentimiento import create_analyzer


MIN_RISK_SCORE = 3

#Definimos los indicadores de corrupcion (o irregularidades) basicos que vamos a buscar en los articulos.
BASE_CORRUPTION_INDICATORS = [
    #delitos economicos y financieros
    "corrupción",
    "fraude",
    "malversación",
    "peculado",
    "desfalco",
    "defraudación",
    "evasión fiscal",
    "evasión de impuestos",
    "lavado de dinero",
    "blanqueo de capitales",
    "financiación ilegal",
    "financiación oculta",

    #sobornos y cohechos
    "soborno",
    "cohecho",
    "coima",
    "cobro de comisiones",
    "comisión ilegal",
    "dádiva",
    "recibo de dádivas",

    #influencias y trafico de influencias
    "tráfico de influencias",
    "colusión",
    "concertación ilícita",
    "puerta giratoria",

    #prevaricación y abuso de poder
    "prevaricación",
    "abuso de poder",
    "omisión de deberes",

    #enriquecimiento y beneficios indebidos
    "enriquecimiento ilícito",
    "enriquecimiento injusto",

    #nepotismo y clientelismo
    "nepotismo",
    "clientelismo",
    "caciquismo",

    #contratación y licitaciones fraudulentas
    "amaño de contratos",
    "licitación amañada",
    "licitación fraudulenta",
    "favoritismo",

    #otros indicadores
    "extorsión",
    "chantaje",
    "organización criminal",
    "inmovilismo",  
    "alerta", 
    "urgencia", 
    "caos"
]


CRITICAL_TERMS = {"fraude", "malversación", "blanqueo de capitales", "corrupción", "soborno", "cohecho", "prevaricación", "enriquecimiento ilícito"}

#Definimos un diccionario que mapea los dominios de las fuentes a sus respectivos modulos de scraping, cada fuente de noticias tiene su propio modulo que define como extraer los enlaces de los articulos y el contenido de cada articulo ya que cada 
#fuente tiene una estructura HTML diferente y puede requerir diferentes selectores o metodos para cargar correctamente el contenido.
SOURCES = {
    "elconfidencial.com": elConfidencial,
    "rtve.es": rtve,
    "20minutos.es": veinteMinutos,
    "defensa.com": defensa, 
    "larazon.es": laRazon,
    "vozpopuli.com": vozPopuli
}

class MultiSourceSpider(scrapy.Spider):
    
    """
Spider que recorrera diversas fuentes de noticias (las definidas en SOURCES),
tambien extrae enlaces de artículos, filtra por términos de contrato + corrupción,
calcula score de riesgo y sentimiento, y retorna los items para ser procesados por el pipeline.

Settings específicos:
    - Usamos Playwright para renderizar javascript y cargar contenido dinámico.
    - definimos un límite de páginas y retrasos para no saturar las webs
    """
    
    name = "multisource_spider"
    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 15000,
        "CLOSESPIDER_PAGECOUNT": 200,
        "DEPTH_LIMIT": 1,
        "DOWNLOAD_DELAY": 2,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 3,
        "AUTOTHROTTLE_MAX_DELAY": 10,
    }

    MAX_PAGES_PER_SOURCE = 1
    MAX_LINKS_PER_PAGE = 30

    # # Normaliza el texto: elimina acentos, convierte a minúsculas, quita puntuación y espacios extra
    # # Devuelve el texto normalizado.
    def normalize(self, text: str) -> str:
        """
    Normalizamos un texto eliminando acentos, pasando a ASCII,
    convirtiendo a minúsculas y quitando puntuación / espacios extra.

    Args:
        text (str): Cadena original.

    Returns:
        str: Texto limpio y normalizado.
        """
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def __init__(self, *args, contract_terms=None, result_path=None, **kwargs):
        """
    Inicializa el spider con los terminos de contrato y la ruta de resultados.

    Args:
        contract_terms (str): Cadena con los terminos separados por comas.
        result_path (str): Ruta del fichero JSON donde volcar el output.
        """
        super().__init__(*args, **kwargs)
        if not contract_terms:
            raise CloseSpider("Debes pasar los terminos del contrato con: -a contract_terms=\"T1,T2,...\"")
        self.result_path = result_path
        #normalizamos los terminos necesarios como los terminos de contrato, los indicadores de corrupcion y los terminos criticos.
        self.contract_terms = {self.normalize(t) for t in contract_terms.split(",")}
        self.corruption_indicators = {self.normalize(kw) for kw in BASE_CORRUPTION_INDICATORS}
        self.critical_terms = {self.normalize(t) for t in CRITICAL_TERMS}
        #inicializamos un contador de páginas procesadas por fuente
        self._pages_done = {domain: 0 for domain in SOURCES}
        #inicializamos el analizador de sentimientos de pysentimiento para analizar el sentimiento de los articulos 
        self.sentiment_analyzer = create_analyzer(task="sentiment", lang="es")

   
    def start_requests(self):
        """
    Generamos aqui las peticiones iniciales a cada dominio de SOURCES.
    Usamos Playwright para renderizado o espera de selectores segun el modulo que estemos utilizando.
        """
        for domain, module in SOURCES.items():
            #cada modulo tiene definida su STAT_URL asi que la pegamos al dominio para iniciar el scraping.
            start_url = getattr(module, "START_URL", f"https://{domain}")
            #si en el modulo hay un selector de lista definido, usamos ese para esperar a que cargue la lista de articulos. sino usamos el estado de carga por defecto
            if hasattr(module, "LIST_SELECTOR"):
                pw_methods = [PageMethod("wait_for_selector", module.LIST_SELECTOR, timeout=15000)]
            else:
                pw_methods = [PageMethod("wait_for_load_state", "domcontentloaded", timeout=15000)]
            #generamos la peticion inicial con Playwright y el callback parse_source.
            yield scrapy.Request(
                start_url,
                callback=self.parse_source,
                errback=self.on_timeout,
                meta={
                    "source_domain": domain,
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": pw_methods,
                }
            )
    
   
    async def parse_source(self, response):
        """
    Parseamos la pagina de listado de artículos de una determinada fuente,
    extraemos los enlaces y reenviamos a parse_article, se define como una funcion asincrona porque necesitamos que interactue con playwright.

    Args:
        response (scrapy.Response): Respuesta de la petición de listado.
        """
        if response.status != 200:
            self.logger.warning(f"Skipping non-200 page {response.status}: {response.url}")
            return
        #obtenemos el dominio de la fuente desde los metadatos de la respuesta
        domain = response.meta["source_domain"]
        #si ya hemos procesado el maximo de paginas para esta fuente, salimos
        self._pages_done[domain] += 1
        if self._pages_done[domain] > self.MAX_PAGES_PER_SOURCE:
            return
        
        #obtenemos el html de la respuesta, si es una pagina de Playwright, usamos su metodo content() para obtener el HTML completo.
        page = response.meta.get("playwright_page")
        html = ""
        if page:
            try:
                html = await page.content()
            finally:
                await page.close()
        #creamos un selector de Scrapy a partir del HTML obtenido, si no hay HTML, usamos el texto de la respuesta.
        selector = scrapy.Selector(text=html or response.text)
        #extraemos los enlaces de los articulos usando el metodo extract_article_links del modulo correspondiente al dominio y limitamos a MAX_LINKS_PER_PAGE.
        links, _ = SOURCES[domain].extract_article_links(selector)
        links = links[: self.MAX_LINKS_PER_PAGE]
        
        self.logger.info(f"{domain}: procesando {len(links)} enlaces (página {self._pages_done[domain]})")
        #para todos los dominios excepto 20minutos.es, usamos Playwright para cargar los articulos, esto es tras haber detectado que 20minutos.es no requiere Playwright para cargar sus articulos correctamente
        for title, link in links:
            meta = {"source_domain": domain, "original_title": title}
            if domain != "20minutos.es":
                meta.update({
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded", timeout=15000)
                    ]
                })
            #enviamos una nueva peticion a cada enlace de articulo, con el callback parse_article y el errback on_timeout.
            yield response.follow(
                link,
                callback=self.parse_article,
                errback=self.on_timeout,
                meta=meta
            )
   
    
    async def parse_article(self, response):
        """
    Extraemos aqui el contenido de un articulo, tambien se filtra por terminos de contrato y corrupcion,
    calculamos puntuaciones de riesgo y sentimiento y generamos un CorruptionItem.

    Args:
        response (scrapy.Response): Respuesta de la petición al artículo.
        """
        if response.status != 200:
            self.logger.warning(f"Skipping non-200 page {response.status}: {response.url}")
            return
        domain = response.meta["source_domain"]
        module = SOURCES[domain]

        page = response.meta.get("playwright_page")
        html = ""
        if page:
            try:
                html = await page.content()
            finally:
                await page.close()

        selector = scrapy.Selector(text=html or response.text)
        #cada modulo tiene su propio metodo para extraer el contenido del articulo, asi que llamamos al metodo correspondiente para cada fuente sino usamos el metodo por defecto
        try:
            title, paragraphs, author, pub_date = module.extract_article_content(selector, response.meta)
        except TypeError:
            title, paragraphs, author, pub_date = module.extract_article_content(selector)
        
        #sino hemos conseguido extraer la fecha de publicacion, intentamos con metadatos alternativos genericos(implementado por problemas con algunos sitios que no tienen el selector de fecha esperado)
        if not pub_date:
            pub_date = selector.xpath('//meta[@property="article:published_time"]/@content').get()
        if not pub_date:
            pub_date = selector.css('time::attr(datetime)').get()
        if not pub_date and domain == "20minutos.es":
            pub_text = selector.css('time.time::text').get()
            if pub_text:
                from datetime import datetime
                try:
                    pub_date = datetime.strptime(pub_text.strip(), '%d/%m/%Y %H:%M').isoformat()
                except ValueError:
                    pub_date = ""
        pub_date = pub_date or ""

        #normalizamos el titulo y el contenido del articulo, eliminamos espacios extra y saltos de linea
        raw_full = " ".join(p.strip() for p in paragraphs if p.strip())
        norm_text = self.normalize(title + " " + raw_full)

        #creamos un conjunto de terminos de contrato encontrados y otro de indicadores de corrupcion encontrados
        found_contract = {
            t for t in self.contract_terms
            if t in norm_text
        }
        if not found_contract:
            return

        found_corr = {
            kw for kw in self.corruption_indicators
            if kw in norm_text
        }
        if not found_corr:
            return

        #calculamos una puntuacion base a partir de los terminos encontrados, asignando 10 puntos por terminos criticos y 5 por terminos normales
        score = sum(10 if kw in self.critical_terms else 5 for kw in found_corr)
        
        #llamamos al analizador de sentimientos de pysentimiento para analizar el sentimiento del texto completo del articulo
        sentiment_result = self.sentiment_analyzer.predict(raw_full)
        
        #sentiment_result.output es el label del sentimiento (ej: 'POS' o 'NEG')
        sentiment_label = sentiment_result.output 
        
        # Guardamos la probabilidad del sentimiento detectado (ej: 0.9 si es 90% negativo, etc)
        pos_proba = sentiment_result.probas.get('POS', 0.0)
        neg_proba = sentiment_result.probas.get('NEG', 0.0)
        #como lo que devuelve pysentimiento es un diccionario con las probabilidades de cada sentimiento, calculamos la polaridad como la diferencia entre la probabilidad positiva y negativa
        #de esta manera, si es positivo, la polaridad sera positiva y si es negativo, la polaridad sera un numero negativo.
        sentiment_polarity = pos_proba - neg_proba

        #ajustamos la puntuación de riesgo segun el sentimiento:
        if sentiment_label == 'NEG':
            #aniadimos hasta 10 puntos extra, proporcionales a que tan negativo es
            score += int(sentiment_result.probas['NEG'] * 10)
        
        #si el score es menor que el minimo, no generamos el item
        if score < MIN_RISK_SCORE:
            return

        #definimos el nivel de alerta segun los terminos encontrados y la puntuacion de riesgo
        if any(kw in self.critical_terms for kw in found_corr):
            level = "CRÍTICA"
        elif score > 15:
            level = "ALTA"
        else:
            level = "MEDIA"

        preview = (title + " " + raw_full)[:800].rstrip() + "…"

        #finalmente creamos el item de Scrapy con los datos extraídos
        #y lo devolvemos para que sea procesado por el pipeline.
        yield CorruptionItem(
            title=title.strip(),
            link=response.url,
            content_preview=preview,
            source=domain,
            author=author,
            publication_date=pub_date,
            contract_terms_found=list(found_contract),
            corruption_keywords_found=list(found_corr),
            sentiment_polarity=round(sentiment_polarity, 2),
            risk_score=score,
            alert_level=level,
        )


    def on_timeout(self, failure):
        """
    Manejador de errores de Playwright: cierra la página si existe,
    y reintenta la petición sin Playwright si procede.

    Args:
        failure: Failure object de Scrapy con la request que ha fallado.
        """
        #si se ha producido un error, obtenemos la request original
        req = failure.request
        #si la request tiene un meta con playwright_page, intentamos cerrarla para liberar recursos.
        page = req.meta.get("playwright_page")
        #para cerrarla al ser page un objeto de Playwright, usamos asyncio para cerrar la pagina asincronamente
        if page:
            try:
                asyncio.get_event_loop().create_task(page.close())
            except Exception:
                pass
        #si la request tiene un meta con playwright, intentamos reintentar la request sin Playwright
        if req.meta.get("playwright"):
            self.logger.info(f"Reintentando SIN Playwright → {req.url}")
            new_meta = {k: v for k, v in req.meta.items() if not k.startswith("playwright")}
            return scrapy.Request(
                req.url,
                callback=req.callback,
                errback=self.on_timeout,
                meta=new_meta,
                dont_filter=True,
            )
        #si ni con Playwright ni sin él simplemente logueamos el error y devolvemos None
        self.logger.warning(f"No pudo cargarse (normal): {req.url} → {failure.value}")
        return None