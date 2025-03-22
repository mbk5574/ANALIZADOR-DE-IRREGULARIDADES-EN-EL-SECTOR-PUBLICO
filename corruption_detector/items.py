import scrapy

class CorruptionItem(scrapy.Item):
    title = scrapy.Field()                  # Título de la noticia
    link = scrapy.Field()                   # URL del artículo
    content_preview = scrapy.Field()        # Resumen del contenido o extracto
    keywords_found = scrapy.Field()         # Lista de palabras clave detectadas
    sentiment_polarity = scrapy.Field()     # Polaridad del sentimiento (-1 negativa, 0 neutral, 1 positiva)
    sentiment_subjectivity = scrapy.Field() # Grado de subjetividad (0 objetivo - 1 subjetivo)
    risk_score = scrapy.Field()             # Índice numérico de riesgo de corrupción
    alert_level = scrapy.Field()            # Nivel de alerta asociado (BAJA, MEDIA, ALTA)
    date_scraped = scrapy.Field()           # Fecha/hora en que se obtuvo la noticia
    source = scrapy.Field()                 # Fuente de la noticia (ej.: "El Confidencial")
