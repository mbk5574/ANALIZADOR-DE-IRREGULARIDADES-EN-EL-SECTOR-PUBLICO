# Fichero: sources/vozPopuli.py

START_URL = "https://www.vozpopuli.com/"

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la portada de vozpopuli.com y devuelve:
      - una lista de tuplas (title, link)
      - None (no hay paginación tradicional)
    """
    articles = selector.css("article")
    result = []
    
    for article in articles:
        link_element = article.css("h2[itemprop='headline'] a")
        
        link = link_element.css("::attr(href)").get()
        title = "".join(link_element.css("::text").getall()).strip()
        
        if link and title:
            full_link = selector.response.urljoin(link)
            result.append((title, full_link))
            
    next_page_link = None
    
    return result, next_page_link


def extract_article_content(obj, meta=None):
    """
    Recibe un scrapy.Response (con .selector) o un scrapy.Selector.
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
        or selector.css("h1[itemprop='headline']::text").get(default="").strip()
    )
    if not title:
        title = context_meta.get("original_title", "")

    paragraphs = selector.css("div.art-cuerpo p::text").getall()

    author = selector.css("a[itemprop='author'] span[itemprop='name']::text").get(default="")
    publication_date = (
        selector.css("meta[itemprop='datePublished']::attr(content)").get(default="")
        or selector.css("time[itemprop='datePublished']::attr(datetime)").get()
        or selector.css("time::attr(datetime)").get()
        or selector.css("span.art-fecha::text").get()
        or ""
    )  

    return title.strip(), paragraphs, author.strip(), publication_date.strip()