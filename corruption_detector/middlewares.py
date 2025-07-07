"""
Middlewares de Scrapy para el proyecto Corruption Detector.
- CorruptionDetectorSpiderMiddleware: hookea (es decir, intercepta) eventos del spider (como el: inicio, cierre, manejo de respuestas y excepciones).
- CorruptionDetectorDownloaderMiddleware: maneja peticiones HTTP (headers, logging, errores de descarga).
"""
from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Response


class CorruptionDetectorSpiderMiddleware:
    """
Middleware de spider que intercepta y registra eventos dentro del ciclo de vida del Spider:
    - process_spider_input: antes de que el spider procese la respuesta.
    - process_spider_output: tras generar items del spider.
    - process_spider_exception: captura excepciones en el spider.
    - process_start_requests: registra las peticiones iniciales.
    - spider_opened / spider_closed: loguea apertura y cierre del spider.
    """
    @classmethod
    def from_crawler(cls, crawler):
        """
    Constructor que utilizaremos para crear una instancia del middleware: conecta las señales de apertura y cierre del spider.
        """
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_spider_input(self, response, spider):
        """
    Se llama antes de que el spider procese una respuesta.
    aqui tan solo registramos la URL.
        """
        spider.logger.debug(f"Processing response URL: {response.url}")
        return None

    def process_spider_output(self, response, result, spider):
        """
    Llamado tras que el spider genere items o nuevas peticiones.
    Registramos cada item emitido.
        """
        for item in result:
            spider.logger.debug(f"Item processed from URL: {response.url} -> {item}")
            yield item

    def process_spider_exception(self, response, exception, spider):
        """
    Se llama si ocurre una excepcion en el spider durante el parseo.
    Registramos el error y continuamos sin interrumpir.
        """
        spider.logger.error(f"Exception caught in spider: {exception} at URL: {response.url}")
        return []

    def process_start_requests(self, start_requests, spider):
        """
    lo llamamos para iterar las peticiones iniciales del spider.
    Registramos cada URL que va a ser solicitada.
        """
        for request in start_requests:
            spider.logger.debug(f"Starting request to URL: {request.url}")
            yield request

    def spider_opened(self, spider):
        """Señal de spider abierto: simplemente es para mostrar un mensaje informativo."""
        spider.logger.info(f"Spider opened: {spider.name}")

    def spider_closed(self, spider):
        """Señal de spider cerrado: para mostrar un mensaje de log."""
        spider.logger.info(f"Spider closed: {spider.name}")


class CorruptionDetectorDownloaderMiddleware:
    """
Middleware de descarga que intercepta el siguiente flujo HTTP:
    - process_request: ajusta headers y loguea la petición.
    - process_response: detecta status inesperados y loguea la respuesta.
    - process_exception: registra errores de descarga.
    - spider_opened / spider_closed: loguea el inicio y fin del middleware.
    """

    @classmethod
    def from_crawler(cls, crawler):
        """
    Constructor: conecta señales de apertura y cierre.
        """
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        """
    Antes de enviar la petición HTTP, asignamos un User-Agent por defecto
    y registramos la URL y los headers(buena practica con la que se ha conseguido evitar que algunas paginas bloqueen el scraping).
        """
        request.headers.setdefault(
            'User-Agent',
            'CorruptionDetectorBot/1.0 (+https://yourdomain.com/bot-info)'
        )
        spider.logger.debug(f"Requesting URL: {request.url} with headers: {request.headers}")
        return None

    def process_response(self, request, response, spider):
        """
    Tras recibir la respuesta HTTP:
        - si el status no es 200, emitimos un warning.
        - y siempre retornamos la respuesta al spider.
        """
        if response.status != 200:
            spider.logger.warning(
                f"Unexpected response status {response.status} for URL: {response.url}. "
                "Passing response to spider for custom handling."
            )
            
            return response

        spider.logger.debug(f"Response received from URL: {response.url}")
        return response

    def process_exception(self, request, exception, spider):
        """
    Si ocurre un error durante la descarga, lo registramos como por ejemplo que se agote el tiempo de espera, url inexistente, etc.
        """
        spider.logger.error(
            f"Downloader error for URL: {request.url} with exception: {exception}"
        )
        
        return None

    def spider_opened(self, spider):
        """Señal de apertura del middleware (inicialización)."""
        spider.logger.info(f"Downloader middleware opened for spider: {spider.name}")

    def spider_closed(self, spider):
        """Señal de cierre del middleware (limpieza)"""
        spider.logger.info(f"Downloader middleware closed for spider: {spider.name}")
