import scrapy


class IndeedspiderSpider(scrapy.Spider):
    name = "indeedSpider"
    allowed_domains = ["www.indeed.com"]
    start_urls = ["https://www.indeed.com"]

    def parse(self, response):
        pass
