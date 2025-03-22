from scrapy import signals
from scrapy.exceptions import IgnoreRequest


class CorruptionDetectorSpiderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_spider_input(self, response, spider):
        spider.logger.debug(f"Processing response URL: {response.url}")
        return None

    def process_spider_output(self, response, result, spider):
        for item in result:
            spider.logger.debug(f"Item processed from URL: {response.url}")
            yield item

    def process_spider_exception(self, response, exception, spider):
        spider.logger.error(f"Exception caught in spider: {exception} at URL: {response.url}")
        pass

    def process_start_requests(self, start_requests, spider):
        for request in start_requests:
            spider.logger.debug(f"Starting request to URL: {request.url}")
            yield request

    def spider_opened(self, spider):
        spider.logger.info(f"Spider opened: {spider.name}")

    def spider_closed(self, spider):
        spider.logger.info(f"Spider closed: {spider.name}")


class CorruptionDetectorDownloaderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        request.headers.setdefault('User-Agent', 'CorruptionDetectorBot/1.0 (+https://yourdomain.com/bot-info)')
        spider.logger.debug(f"Requesting URL: {request.url} with headers: {request.headers}")
        return None

    def process_response(self, request, response, spider):
        if response.status != 200:
            spider.logger.warning(f"Unexpected response status {response.status} for URL: {response.url}")
            raise IgnoreRequest(f"Ignoring request due to status: {response.status}")

        spider.logger.debug(f"Response received from URL: {response.url}")
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.error(f"Request failed for URL: {request.url} with exception: {exception}")
        pass

    def spider_opened(self, spider):
        spider.logger.info(f"Downloader middleware active for spider: {spider.name}")