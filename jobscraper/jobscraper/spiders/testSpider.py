import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class TestspiderSpider(scrapy.Spider):
    name = "testSpider"

    def start_requests(self):
        url = r"https://www.linkedin.com/jobs/view/creative-manager-at-uniqlo-4232936215?position=3&pageNum=0&refId=KpPRhDApm5BvkwjWZGV1%2Bg%3D%3D&trackingId=onAMwMYaqnotlCy8OUX%2F1g%3D%3D"
        yield SeleniumRequest(url=url,
                              callback=self.parse,
                              wait_time=10, 
                              wait_until=EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'num-applicants__caption')]"))
        )

    def parse(self, response):

        jobInfo = response.css("div.details")

        card = jobInfo.css("div[class*='info']")[1]
        description = jobInfo.css("div")
        

        # card has title, company, location, time posted, numApplicants, apply / save hrefs.
        title = card.css("h1[class*='title']::text").get().strip()
        company = card.css("a[class*='org-name']::text").get().strip()
        location = card.css("span[class*='bullet']::text").get().strip()
        timePosted = card.css("span[class*='posted-time']::text").get().strip()
        numApplications = response.xpath("//*[contains(@class, 'num-applicants__caption')]/text()").get().strip()
        
        
        
        
        things = [title, company, location, timePosted, numApplications]

        for thing in things:
            print(thing)

        print("*"*25 + "*"*25)


