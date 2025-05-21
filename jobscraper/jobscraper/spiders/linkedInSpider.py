import scrapy
from jobscraper.items import JobItem
from scrapy.selector import Selector

# selenium imports for waiting on requests 
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# misc
import re
import time


class LinkedinspiderSpider(scrapy.Spider):
    name = "linkedInSpider"
    allowed_domains = ["www.linkedin.com"]
    start_urls = ["https://www.linkedin.com/jobs/search/"]


    def parse(self, response):
        
        driver = response.meta['driver']    # makes the page generate dynamic content 
        lastJobScraped = 0                  # tracks the next job to start scraping at
        ACTION_PAUSE_SECONDS = 2            # time between page scrolls (wait for the jobs to load)


        while True:
            
            page = driver.page_source
            sel = Selector(text=page)
            jobs = sel.css("ul[class*='jobs-search__results-list'] li")
            numJobs = len(jobs)


            # case of nothing to scrape
            if numJobs == 0:
                break  
            

            # for loop iterates from the first not-scraped job to the last job available,
            # skipping previously-scraped jobs
            for jobIndex in range(lastJobScraped, numJobs):
                job = jobs[jobIndex]
                jobLink = job.css('a::attr(href)').get().strip()

                # page contains dynamic content; 
                # By.XPATH finds this content and waits for it to render before requesting the page
                # wait_time is a heuristic that skips the page if the content doesn't render in less than 10 seconds
                yield SeleniumRequest(url=jobLink,
                              callback=self.parseJob,
                              wait_time=10, 
                              wait_until=EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'num-applicants__caption')]"))
                )

            # ensures next for loop starts at an unseen job index
            lastJobScraped = numJobs


            try:
                # button is present ==> scrolling doesn't make more jobs ==> button click makes more jobs
                button = driver.find_element(By.XPATH, "//button[contains(@class, '__show-more-button')]")
                button.click()
                time.sleep(ACTION_PAUSE_SECONDS)
            
            except Exception:
                # button is not present ==> scrolling makes more jobs appear
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(ACTION_PAUSE_SECONDS)

            
            page = driver.page_source
            sel = Selector(text=page)
            newJobs = len(sel.css("ul[class*='jobs-search__results-list'] li"))


            # checks if driver process caused dynamic content to generate. if not, kill program
            if newJobs == lastJobScraped:
                break
        
            

    def parseJob(self, response):
       
       
        # this clause checks if the listing is still accepting applications
        # if it is not the listing item is skipped
        if response.css("figure[class*='closed']").get() is not None:
            print("no longer accepting applications")
            #return



        # job object will be our abstract datatype for representing job postings
        job = JobItem()
        


        # parses the id from the url, gets the url in a neater / shorter form
        regex = r"\d+"
        id = re.findall(regex, response.url.split("?")[0])[0]
        url = f"https://linkedin.com/jobs/view/{id}"
        


        # page can be broken into card and description sections
        card = response.css("div[class*='info']")[1]
        description = response.css("div[class*='posting__details']")
        
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
                  and keyword.strip() != '']

        # pulling industries data
        # I'm formatting industries as a list of keywords
        l = criteria[3].css('span::text').get().strip().split(", ")
        s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
        l.pop()
        industries = [keyword.strip() for keyword in l + s 
                  if keyword is not None 
                  and keyword.strip() != '']



        # parsing the description for the salary
        # getting the description text as one string w/out the html characters
        descAsString = " ".join(
            [string.get().strip() 
             for string in description.css("* *::text") 
             if string.get() is not None
             and string.get().strip() is not None])
        

        # regex breakdown:
        # (?:\$|£|€|₹|¥)? | looks for an optional currency indicator. if present, it is a part of the capture
        # \s*\d{1,3}      | allows for any (including none) amount of whitespace between currency indicator and a number with 1 to 3 decimal places. this number must exist for the capture to happen
        # (?:,\d{3})*     | allows for any (including none) amount of groupings of 3 numbers followed by a comma. if present, it is a part of the capture
        # (?:\.\d+)?      | allows for zero or one pattern of a decimal point "." followed by at least one number. if present, it is a part of the capture
        # (?:\s*/\s*(?i:hr|hour|yr|year|mo|month))? | allows for any (including none) whitespace followed by a slash "/", the same whitespace clause, and then a case-insensitive string from the following. all of it is optional. this captures the rate of the pay
        # (?:\s*(?:-|to)\s* | allows for any amount of whitespace followed by a range indicator ("-" or "to") followed by any amount of whitespace
        # the rest is the same as before, but repeated for the second number in the range. 
        # The clause starting with the previous explanation ends after the 2nd number's regex, and is entirely optional

        # edge cases it will fail: it technically captures any number on the page. as a heuristic, I always take the biggest match and require this match to be at least 9 characters.
        # This is no means perfect but rides the edge of excluding valid salaries at the expense of not collecting false data. This heuristic can be tweaked without error to the code
        regex = r"(?:\$|£|€|₹|¥)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*/\s*(?i:hr|hour|yr|year|mo|month))?(?:\s*(?:-|to)\s*(?:\$|£|€|₹|¥)?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*/\s*(?i:hr|hour|yr|year|mo|month))?)?"
        possibleSalaries = sorted(re.findall(regex, descAsString), key=len) # puts the longest match (most likely to be salary) at the back

        salary = possibleSalaries[-1].strip() if possibleSalaries is not [] and len(possibleSalaries[-1].strip()) > 8 else None



        # assigning the Job item its fields appropriately
        # all fields have been stripped of whitespace but no other formatting (except as list items for certain fields) has been applied
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
        
        # an easy way to iterate through the job object
        keys = ['company', 'location', 'numApplicants', 'scrapedFrom', 'timePosted', 'title', 
            'url', 'salary', 'fields', 'level', 'employment', 'industries']
        keys.sort()

        print("*"*25 + "*"*25)
        print("result of scraping link\n")
        
        for key in keys:
            print(f"{key:<20}| {job[key]}")

        print("*"*25 + "*"*25)

    
