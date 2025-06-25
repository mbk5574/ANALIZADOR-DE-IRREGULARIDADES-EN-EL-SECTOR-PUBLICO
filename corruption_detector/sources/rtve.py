# sources/rtve.py

START_URL = "https://www.rtve.es/noticias/"

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la portada de RTVE y devuelve:
      - lista de (title, link)
      - None (no paginación en portada)
    """
    articles = selector.css("article.cell")
    result = []
    for art in articles:
        link = art.css("h3 a::attr(href)").get()
        title = art.css("h3 a span.maintitle::text").get(default="").strip()
        if link and title:
            result.append((title, link))
    return result, None

def extract_article_content(selector):
    """
    Recibe un scrapy.Selector de un artículo de RTVE y devuelve:
      (title, [paragraphs], "", "")
    """
    title = (
        selector.css("meta[property='og:title']::attr(content)").get()
        or selector.css("h1::text").get(default="").strip()
    )
    paragraphs = selector.css("div.mainContent div.artBody p::text").getall()
    return title, paragraphs, "", ""
