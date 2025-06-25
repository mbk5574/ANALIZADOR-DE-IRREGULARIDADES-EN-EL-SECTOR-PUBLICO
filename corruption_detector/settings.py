# settings.py (Versión corregida y simplificada respecto a la otra)

BOT_NAME = "corruption_detector"
SPIDER_MODULES = ["corruption_detector.spiders"]
NEWSPIDER_MODULE = "corruption_detector.spiders"

# --- Configuración General del Bot ---
USER_AGENT = "CorruptionDetectorBot/1.0 (+https://tudominio.com)"
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
COOKIES_ENABLED = False
LOG_LEVEL = "INFO"
FEED_EXPORT_ENCODING = "utf-8"

# --- Configuración de Concurrencia ---
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# --- Pipelines
ITEM_PIPELINES = {
   "corruption_detector.pipelines.TextCleanerPipeline": 200,
   "corruption_detector.pipelines.CorruptionDetectorPipeline": 300,
}


# 1. Asigna los manejadores de descarga a Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# 2. Activa el reactor de Twisted compatible con asyncio
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# 3.Configuramos el tipo de navegador a usar
PLAYWRIGHT_BROWSER_TYPE = "chromium"