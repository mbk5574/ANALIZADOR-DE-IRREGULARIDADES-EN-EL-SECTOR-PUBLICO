# sources/veinte_minutos.py

def extract_article_links(selector):
    """
    Extrae los enlaces y títulos de artículos de 20minutos.
    Devuelve una lista de tuplas: (título, enlace).
    """
    articles = selector.css("article.media, article.media.media-big")
    result = []
    for article in articles:
        link_element = article.css("h1 a, figure a")
        link = link_element.css("::attr(href)").get()
        title = link_element.css("::text").get(default="").strip()
        if title and link:
            result.append((title, link))
    return result

def extract_article_content(selector):
    """
    Extrae el título y párrafos de un artículo de 20minutos.
    Devuelve: (título, lista_de_parrafos).
    """
    title = selector.css("h1.article-title::text").get(default="").strip()
    paragraphs = selector.css(
        'div.article-body p::text, div.article-content p::text, '
        'p.paragraph::text, p.interview-line::text, h2.paragraph-ladillo::text'
    ).getall()
    return title, paragraphs
