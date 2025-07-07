# sources/veinteMinutos.py

START_URL = "https://www.20minutos.es/"

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la portada de 20minutos y devuelve:
      - lista de (title, link)
      - None (no paginación en portada)
    """
    articles = selector.css("article.media, article.media.media-big")
    result = []
    for art in articles:
        link = art.css("h1 a::attr(href), figure a::attr(href)").get()
        title = art.css("h1 a::text, figure a::text").get(default="").strip()
        if link and title:
            result.append((title, link))
    return result, None

def extract_article_content(selector, meta=None):
    """
    Recibe un scrapy.Selector de un artículo de 20minutos y devuelve:
      (title, [paragraphs], "", "")
    """
    title = (
        selector.css("meta[property='og:title']::attr(content)").get()
        or selector.css("h1.article-title::text").get(default="").strip()
    )
    paragraphs = selector.css(
        "div.article-body p::text, div.article-content p::text, "
        "p.paragraph::text, p.interview-line::text, h2.paragraph-ladillo::text"
    ).getall()
    return title, paragraphs, "", ""