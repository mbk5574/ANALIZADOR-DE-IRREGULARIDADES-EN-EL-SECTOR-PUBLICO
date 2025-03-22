BOT_NAME = "corruption_detector"

SPIDER_MODULES = ["corruption_detector.spiders"]
NEWSPIDER_MODULE = "corruption_detector.spiders"

# Identificación del scraper (buena práctica)
USER_AGENT = "CorruptionDetectorBot/1.0 (+https://tudominio.com)"

# Respeta las reglas de robots.txt siempre que sea posible (práctica recomendada)
ROBOTSTXT_OBEY = True

# Control de saturación del servidor
DOWNLOAD_DELAY = 2  # 2 segundos entre peticiones
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False  # Activa solo para depurar

# Codificación UTF-8 para exportaciones
FEED_EXPORT_ENCODING = "utf-8"

# Uso del reactor Asyncio moderno
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Pipelines activados (incluyendo TextCleanerPipeline recomendado anteriormente)
ITEM_PIPELINES = {
    "corruption_detector.pipelines.TextCleanerPipeline": 200,
    "corruption_detector.pipelines.CorruptionDetectorPipeline": 300,
}

# Desactivar cookies si no son necesarias (opcional pero recomendable)
COOKIES_ENABLED = False

# Logging recomendado (nivel INFO o DEBUG según la etapa)
LOG_LEVEL = "INFO"

# Puedes activar HTTP Cache para optimizar pruebas (opcional pero útil en desarrollo)
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hora
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = [500, 503]
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"
