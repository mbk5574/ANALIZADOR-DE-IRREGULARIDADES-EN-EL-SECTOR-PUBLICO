BOT_NAME = "corruption_detector"

SPIDER_MODULES = ["corruption_detector.spiders"]
NEWSPIDER_MODULE = "corruption_detector.spiders"

# Identificación del scraper
USER_AGENT = "CorruptionDetectorBot/1.0 (+https://tudominio.com)"


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

# Pipelines activados 
ITEM_PIPELINES = {
    "corruption_detector.pipelines.TextCleanerPipeline": 200,
    "corruption_detector.pipelines.CorruptionDetectorPipeline": 300,
}

COOKIES_ENABLED = False

# Logging recomendado (nivel INFO o DEBUG según la etapa)
LOG_LEVEL = "INFO"


