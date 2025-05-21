import scrapy
from jobscraper.items import JobItem
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import re

class TestspiderSpider(scrapy.Spider):
    name = "testSpider"

    def start_requests(self):
        url = r"https://www.linkedin.com/jobs/view/sales-manager-on-premise-national-accounts-at-fiji-water-4233859937?position=4&pageNum=0&refId=CeeBBJ6qQfCnPXPm9%2FJ%2Bwg%3D%3D&trackingId=wtLLgyi%2FhXMBY0%2BvhR4ITA%3D%3D"
        yield SeleniumRequest(url=url,
                              callback=self.parse,
                              wait_time=10, 
                              wait_until=EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'num-applicants__caption')]"))
        )
    
    def parse(self, response):
        
        if response.css("figure[class*='closed']").get() is not None:
            print("no longer accepting applications")
            #return

        job = JobItem()
        
        # parses the id from the url, gets the url in a neater / shorter form
        regex = r"\d+"
        id = re.findall(regex, response.url.split("?")[0])[0]
        url = f"https://linkedin.com/jobs/view/{id}"
        
        # page can be broken into card and desc sections
        jobInfo = response.css("div.details")
        card = jobInfo.css("div[class*='info']")[1]
        description = jobInfo.css("div[class*='posting__details']")
        
        # pulling data from card
        # card has title, company, location, time posted, numApplicants, apply / save hrefs.
        title = card.css("h1[class*='title']::text").get().strip()
        company = card.css("a[class*='org-name']::text").get().strip()
        location = card.css("span[class*='bullet']::text").get().strip()
        timePosted = card.css("span[class*='posted-time']::text").get().strip()
        numApplicants = response.xpath("//*[contains(@class, 'num-applicants__caption')]/text()").get().strip()


        # pulling data from description
        # criteria gets us area, level, employment, and industries
        # after I parse the whole description for the pay range using regex (BLEHHH)
        criteria = description.css("ul[class*='criteria'] li")

        # pulls the level and employment data
        level = criteria[0].css('span::text').get().strip()
        employment = criteria[1].css('span::text').get().strip()
        
        # pulling fields data
        # I'm formatting fields as a list of keywords
        l = criteria[2].css('span::text').get().strip().split(", ")
        s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
        l.pop()
        fields = [keyword.strip() for keyword in l + s 
                  if keyword is not None 
                  and keyword.strip() is not '']

        # pulling industries data
        # I'm formatting industries as a list of keywords
        l = criteria[3].css('span::text').get().strip().split(", ")
        s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
        l.pop()
        industries = [keyword.strip() for keyword in l + s 
                  if keyword is not None 
                  and keyword.strip() is not '']



        # parsing the description for the salary
        # getting the description text as one string w/out the html characters
        descAsString = " ".join(
            [string.get().strip() 
             for string in description.css("* *::text") 
             if string.get() is not None
             and string.get().strip() is not None])
        
        regex = r"(?:\$|£|€|₹|¥)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*/\s*(?i:hr|hour|yr|year|mo|month))?(?:\s*(?:-|to)\s*(?:\$|£|€|₹|¥)?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*/\s*(?i:hr|hour|yr|year|mo|month))?)?"
        salaryOrNone = sorted(re.findall(regex, descAsString), key=len) # puts the longest match (most likely to be salary) at the back

        salary = salaryOrNone[-1].strip() if salaryOrNone is not [] and len(salaryOrNone[-1].strip()) > 5 else None



        # assigning the Job item its fields appropriately
    
        job['url'] = url
        job['title'] = title
        job['level'] = level
        job['salary'] = salary
        job['fields'] = fields
        job['company'] = company
        job['location'] = location
        job['employment'] = employment
        job['timePosted'] = timePosted
        job['industries'] = industries
        job['scrapedFrom'] = {"linkedIn": id}
        job['numApplicants'] = numApplicants
        
        keys = ['company', 'location', 'numApplicants', 'scrapedFrom', 'timePosted', 'title', 
            'url', 'salary', 'fields', 'level', 'employment', 'industries']
        keys.sort()

        print("*"*25 + "*"*25)
        print("result of scraping link\n")
        
        for key in keys:
            print(f"{key:<20}| {job[key]}")

        print("*"*25 + "*"*25)

        


