# Fichero: sources/laRazon.py

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la portada de larazon.es y devuelve:
      - una lista de tuplas (title, link)
      - None (no hay paginación tradicional)
    """
    articles = selector.css("article")
    result = []
    
    for article in articles:
        #el título y el enlace suelen estar en un <a> dentro de un h2 o h3
        link_element = article.css("h2.article__title a, h3.article__title a")
        
        link = link_element.css("::attr(href)").get()
        title = "".join(link_element.css("::text").getall()).strip()
        
        if link and title:
            #los enlaces pueden ser relativos, así que los completamos
            full_link = selector.response.urljoin(link)
            result.append((title, full_link))
            
    #si no se ha detectado un sistema de paginación simple en la portada.
    next_page_link = None
    
    return result, next_page_link

def extract_article_content(obj, meta=None):
    """
    Recibe un scrapy.Response (con .selector y .meta) o un scrapy.Selector.
    Devuelve (title, [paragraphs], author, publication_date).
    """
    
    if hasattr(obj, "selector"):
        selector = obj.selector
        context_meta = getattr(obj, "meta", {}) or {}
    else:
        selector = obj
        context_meta = meta or {}

    title = (
        selector.css("meta[property='og:title']::attr(content)").get()
        or selector.css("h1.article-main__title::text").get(default="").strip()
    )
    if not title:
        title = context_meta.get("original_title", "")

    paragraphs = selector.css("div.article-main__content p::text").getall()

    author = selector.css("span.article-author__name a::text").get(default="")
    publication_date = selector.css(
        "meta[property='article:published_time']::attr(content)"
    ).get(default="")

    return title.strip(), paragraphs, author.strip(), publication_date.strip()
