# sources/defensa.py

START_URL = "https://www.defensa.com/"

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la portada de defensa.com y devuelve:
      - lista de tuplas (title, link)
      - link a la siguiente página (o None)
    """
    articles = selector.css("article.content-list, article.content-grid")
    result = []
    for article in articles:
        link = article.css("h3 > a.e_titul::attr(href)").get()
        title = (
            article.css("h3 > a.e_titul::text").get(default="").strip()
        )
        if link and title:
            if not link.startswith("http"):
                link = "https://www.defensa.com" + link
            result.append((title, link))
    
    next_page = selector.css("a.next-page::attr(href)").get()
    return result, next_page

def extract_article_content(selector, meta=None):
    """
    Recibe un scrapy.Selector de un artículo individual y devuelve:
      (title, [paragraphs], author, publication_date)
    """
    title = (
        selector.css("meta[property='og:title']::attr(content)").get()
        or selector.css("h1.entry-title::text").get(default="").strip()
    )
    paragraphs = selector.css("div.entry-content p::text").getall()
    author = selector.css("span.entry-meta-author::text").get(default="").strip()
    publication_date = selector.css("time.updated::attr(datetime)").get(default="").strip()

    return title, paragraphs, author, publication_date
