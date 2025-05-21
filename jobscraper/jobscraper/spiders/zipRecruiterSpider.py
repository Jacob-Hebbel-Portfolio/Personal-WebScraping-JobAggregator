import scrapy


class ZiprecruiterspiderSpider(scrapy.Spider):
    name = "zipRecruiterSpider"
    allowed_domains = ["www.ziprecruiter.com"]
    start_urls = ["https://www.ziprecruiter.com"]

    def parse(self, response):
        pass
