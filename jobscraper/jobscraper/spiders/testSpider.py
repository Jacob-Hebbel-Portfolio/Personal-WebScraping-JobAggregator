import scrapy
from scrapy_selenium import SeleniumRequest

class TestspiderSpider(scrapy.Spider):
    name = "testSpider"

    def start_requests(self):
        url = r"https://www.linkedin.com/jobs/view/creative-manager-at-uniqlo-4232936215?position=3&pageNum=0&refId=KpPRhDApm5BvkwjWZGV1%2Bg%3D%3D&trackingId=onAMwMYaqnotlCy8OUX%2F1g%3D%3D"
        yield SeleniumRequest(url=url, callback=self.parse, wait_time=10)

    def parse(self, response):

        jobPage = response.css("main section div")

        card = jobPage.css("section")[1].css("div div div")
        description = jobPage.css("div")

        
        # card has role, company, location, time posted, numApplicants, apply / save hrefs.
        role = card.css("h1::text").get().strip()
        company = card.css("h4 div a::text").get().strip()
        location = card.css("h4 div span::text").get().strip()
        timePosted = card.css()

    def async_parse(self, response):
        print("starting process")


