import scrapy


class IndeedScraperSpider(scrapy.Spider):
    name = "indeed-scraper"
    allowed_domains = ["www.indeed.com"]
    start_urls = ["https://www.indeed.com/"]

    def parse(self, response):
        pass
