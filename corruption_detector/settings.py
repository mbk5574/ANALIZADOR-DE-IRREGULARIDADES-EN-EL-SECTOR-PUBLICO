# corruption_detector/settings.py

BOT_NAME = "corruption_detector"
SPIDER_MODULES = ["corruption_detector.spiders"]
NEWSPIDER_MODULE = "corruption_detector.spiders"

USER_AGENT = "CorruptionDetectorBot/1.0 (+https://tudominio.com)"
ROBOTSTXT_OBEY = True  
DOWNLOAD_DELAY = 2
COOKIES_ENABLED = False
LOG_LEVEL = "INFO"

# Pipelines — primero limpio, luego vuelco el JSON
ITEM_PIPELINES = {
    "corruption_detector.pipelines.TextCleanerPipeline": 100,
    "corruption_detector.pipelines.CorruptionDetectorPipeline": 200,
}

# Deshabilito el exportador de feeds interno de Scrapy
# para evitar que intente escribir por FEED_URI.
EXTENSIONS = {
    "scrapy.extensions.feedexport.FeedExporter": None,
}

# Handlers de Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Control de crawling
DEPTH_LIMIT = 1
CLOSESPIDER_PAGECOUNT = 200

# AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Ajustes de Playwright
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 15000  # 15 s
PLAYWRIGHT_MAX_CONTEXTS = 1
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4
PLAYWRIGHT_BROWSER_TYPE = "chromium"

FEED_URI = ""
