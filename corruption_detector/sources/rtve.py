# sources/rtve.py

START_URL = "https://www.rtve.es/noticias/"

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la página de listado y devuelve:
      - lista de tuplas (title, link)
      - link a la siguiente página (o None)
    """
    result = []
    for a in selector.css("a"):
        href = a.attrib.get("href", "")
        title = a.css("::text").get(default="").strip()

        if "/noticias/" not in href:
            continue

        if href and title:
            if not href.startswith("http"):
                href = "https://www.rtve.es" + href
            result.append((title, href))

    next_page = selector.css("a.next-page-link::attr(href)").get()
    if next_page and not next_page.startswith("http"):
        next_page = "https://www.rtve.es" + next_page

    return result, next_page

def extract_article_content(selector, meta=None):
    """
    Recibe un scrapy.Selector de un artículo individual y devuelve:
      (title, [paragraphs], author, publication_date)
    """
    title = (
        selector.css("meta[property='og:title']::attr(content)").get()
        or selector.css("h1::text").get(default="").strip()
    )
    paragraphs = selector.css("div.article-content p::text").getall()
    author = selector.css("span.author__name::text").get(default="").strip()
    publication_date = selector.css("time::attr(datetime)").get(default="").strip()

    return title, paragraphs, author, publication_date
