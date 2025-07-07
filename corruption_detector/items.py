import scrapy

class CorruptionItem(scrapy.Item):
    """
Definición de los item de Scrapy que representan la informacion extraida
de cada artículo web durante el scraping.

Cada campo correspondera a una propiedad que luego pasará por los pipelines
para su normalización, enriquecimiento y posterior volcado a JSON/CSV.
    """
    title = scrapy.Field()
    link = scrapy.Field()
    content_preview = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    publication_date = scrapy.Field()
    contract_terms_found = scrapy.Field()
    corruption_keywords_found = scrapy.Field()
    sentiment_polarity = scrapy.Field()
    risk_score = scrapy.Field()
    date_scraped = scrapy.Field()  
    entities = scrapy.Field()
    alert_level = scrapy.Field()
    indicator_count = scrapy.Field()
    content_length = scrapy.Field()
