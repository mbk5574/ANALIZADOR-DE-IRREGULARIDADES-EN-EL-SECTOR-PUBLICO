# sources/elConfidencial.py

START_URL = "https://www.elconfidencial.com/espana/"

def extract_article_links(selector):
    """
    Recibe un scrapy.Selector de la página de listado y devuelve:
      - lista de tuplas (title, link)
      - link a la siguiente página (o None)
    """
    articles = selector.css("article")
    result = []
    for article in articles:
        link = article.css("a::attr(href)").get()
        title = (
            article.css("a::attr(data-title)").get()
            or article.css("h1::text, h2::text, h3::text").get(default="").strip()
        )
        if link and title:
            result.append((title.strip(), link))
    next_page = selector.css("a.next-page-link::attr(href)").get()
    return result, next_page

def extract_article_content(selector):
    """
    Recibe un scrapy.Selector de un artículo individual y devuelve:
      (title, [paragraphs], author, publication_date)
    """
    title = (
        selector.css("meta[property='og:title']::attr(content)").get()
        or selector.css("h1::text").get(default="").strip()
    )
    paragraphs = selector.css(
        "div.news-body p::text, div#news-body-cc p::text"
    ).getall()
    author = selector.css(
        "div.author-name span::text, a.author-link::text"
    ).get(default="").strip()
    publication_date = selector.css("time::attr(datetime)").get(default="").strip()
    return title, paragraphs, author, publication_date
