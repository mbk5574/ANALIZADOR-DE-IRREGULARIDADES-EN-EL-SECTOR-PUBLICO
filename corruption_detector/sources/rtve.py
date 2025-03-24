# sources/rtve.py

def extract_article_links(selector):
    """
    Extrae los enlaces y títulos de artículos de RTVE.
    Devuelve una lista de tuplas: (título, enlace).
    """
    articles = selector.css("article.cell")
    result = []
    for article in articles:
        title = article.css("h3 a span.maintitle::text").get(default="").strip()
        link = article.css("h3 a::attr(href)").get()
        if title and link:
            result.append((title, link))
    return result

def extract_article_content(selector, response_meta):
    """
    Extrae el contenido de un artículo de RTVE.
    El título se extrae de meta (porque se guardó en parse_source).
    Devuelve: (título, lista_de_parrafos).
    """
    title = response_meta.get("article_title", "")
    paragraphs = selector.css("div.mainContent div.artBody p::text").getall()
    return title, paragraphs
