# corruption_detector/spiders/multisource_spider.py

import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.exceptions import CloseSpider
from textblob import TextBlob
from corruption_detector.items import CorruptionItem
from corruption_detector.sources import elConfidencial, rtve, veinteMinutos

BASE_CORRUPTION_INDICATORS = [
    "corrupción", "fraude", "malversación", "soborno",
    "tráfico de influencias", "enriquecimiento ilícito",
    "blanqueo de capitales", "prevaricación", "cohecho", "financiación ilegal"
]
CRITICAL_TERMS = {"fraude", "malversación", "blanqueo de capitales"}

SOURCES = {
    "elconfidencial.com": elConfidencial,
    "rtve.es": rtve,
    "20minutos.es": veinteMinutos,
}


class MultiSourceSpider(scrapy.Spider):
    name = "multisource_spider"
    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,  # 30 s por navegación
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ct = kwargs.get("contract_terms", "").strip()
        if not ct:
            raise CloseSpider("Debes pasar -a contract_terms=\"T1,T2,...\"")
        self.contract_terms = {t.lower() for t in ct.split(",")}
        self.corruption_indicators = set(map(str.lower, BASE_CORRUPTION_INDICATORS))
        self.critical_terms = CRITICAL_TERMS

    def start_requests(self):
        for domain, module in SOURCES.items():
            start_url = getattr(module, "START_URL", f"https://www.{domain}")

            # Si el módulo define LIST_SELECTOR, esperamos a ese selector;
            # si no, a DOMContentLoaded.
            if hasattr(module, "LIST_SELECTOR"):
                page_methods = [
                    PageMethod(
                        "wait_for_selector",
                        module.LIST_SELECTOR,
                        timeout=30000
                    )
                ]
            else:
                page_methods = [
                    PageMethod(
                        "wait_for_load_state",
                        "domcontentloaded",
                        timeout=30000
                    )
                ]

            yield scrapy.Request(
                start_url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": page_methods,
                    "source_domain": domain,
                },
                callback=self.parse_source,
            )

    async def parse_source(self, response):
        domain = response.meta["source_domain"]
        module = SOURCES[domain]

        page = response.meta.get("playwright_page")
        html = ""
        try:
            if page:
                html = await page.content()
        except Exception as e:
            self.logger.warning(f"{domain}: fallo al esperar selector, usando HTML simple ({e})")
        finally:
            if page:
                await page.close()

        selector = scrapy.Selector(text=html or response.text)
        links, next_page = module.extract_article_links(selector)
        self.logger.info(f"{domain}: {len(links)} enlaces encontrados")

        for title, link in links:
            # Para 20minutos no usamos Playwright en el artículo (evitamos así timeouts)
            if domain == "20minutos.es":
                yield response.follow(
                    link,
                    callback=self.parse_article,
                    meta={
                        "source_domain": domain,
                        "original_title": title,
                    },
                )
            else:
                # El resto de dominios sí usan Playwright en el artículo
                yield response.follow(
                    link,
                    callback=self.parse_article,
                    meta={
                        "source_domain": domain,
                        "original_title": title,
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod(
                                "wait_for_load_state",
                                "domcontentloaded",
                                timeout=30000
                            )
                        ],
                    },
                )

        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_source,
                meta={"source_domain": domain}
            )

    async def parse_article(self, response):
        domain = response.meta["source_domain"]
        module = SOURCES[domain]

        # 1) Obtener HTML (Playwright o normal)
        page = response.meta.get("playwright_page")
        html = ""
        if page:
            try:
                html = await page.content()
            finally:
                await page.close()

        selector = scrapy.Selector(text=html or response.text)

        # 2) Llamada al extractor, con o sin response.meta
        try:
            title, paragraphs, author, pub_date = module.extract_article_content(selector, response.meta)
        except TypeError:
            title, paragraphs, author, pub_date = module.extract_article_content(selector)

        # 3) Análisis común
        full_content = " ".join(p.strip() for p in paragraphs if p.strip())
        text_to_analyze = (title + " " + full_content).lower()

        found_contract = {t for t in self.contract_terms if t in text_to_analyze}
        if not found_contract:
            return
        found_corr = {kw for kw in self.corruption_indicators if kw in text_to_analyze}
        if not found_corr:
            return

        polarity = TextBlob(full_content).polarity
        subjectivity = TextBlob(full_content).subjectivity
        score = sum(10 if kw in self.critical_terms else 5 for kw in found_corr)
        if polarity < -0.4:
            score += 7
        if score < 3:
            return

        if any(kw in self.critical_terms for kw in found_corr):
            level = "CRÍTICA"
        elif score > 15:
            level = "ALTA"
        else:
            level = "MEDIA"

        preview = (title + " " + full_content)[:800].rstrip() + "…"

        yield CorruptionItem(
            title=title.strip(),
            link=response.url,
            content_preview=preview,
            source=domain,
            author=author,
            publication_date=pub_date,
            contract_terms_found=list(found_contract),
            corruption_keywords_found=list(found_corr),
            sentiment_polarity=round(polarity, 2),
            sentiment_subjectivity=round(subjectivity, 2),
            risk_score=score,
            alert_level=level,
        )
