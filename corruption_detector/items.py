import scrapy

class CorruptionItem(scrapy.Item):
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
    alert_level = scrapy.Field()
    date_scraped = scrapy.Field()  
    sentiment_subjectivity = scrapy.Field()  

