import scrapy


class ZiprecruiterScraperSpider(scrapy.Spider):
    name = "zipRecruiter-scraper"
    allowed_domains = ["www.ziprecruiter.com"]
    start_urls = ["https://www.ziprecruiter.com/"]

    def parse(self, response):
        pass
