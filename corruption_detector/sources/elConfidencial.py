# sources/confidencial.py

def extract_article_links(selector):
    """
    Extrae los enlaces y títulos de artículos de El Confidencial.
    Devuelve una lista de tuplas: (título, enlace).
    """
    articles = selector.css("article, div.article-item, div.news-card")
    result = []
    for article in articles:
        title = article.css("h2::text, h3::text").get(default="").strip()
        link = article.css("a::attr(href)").get()
        if title and link:
            result.append((title, link))
    return result

def extract_article_content(selector):
    """
    Extrae el título y los párrafos de un artículo de El Confidencial.
    Devuelve: (título, lista_de_parrafos).
    """
    og_title = selector.css('meta[property="og:title"]::attr(content)').get('')
    title = og_title or selector.css('h1::text').get(default="").strip()
    paragraphs = selector.css('div#news-body-cc p::text').getall()
    return title, paragraphs
