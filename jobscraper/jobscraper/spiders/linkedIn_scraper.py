import scrapy
from scrapy_selenium import SeleniumRequest

class LinkedinScraperSpider(scrapy.Spider):
    name = "linkedIn-scraper"
    allowed_domains = ["www.linkedin.com"]
    start_urls = ["https://www.linkedin.com/jobs/search/"]

    def parse(self, response):
        
        mostRecentJob = 0
        
        while True:
            
            jobs = response.css(".jobs-search__results-list li")
            newJobs = jobs[mostRecentJob:]

            for job in newJobs:

                jobPage = job.css("div a::attr(href)")
                yield response.follow(jobPage, callback=self.parseJobPage)
                
            mostRecentJob = len(jobs)

            # call to selenium web driver to scroll, dynamically adding more jobs to the page
            # when it loops, jobs will have a bigger length, with new jobs at the end
            # mostRecentJob gets the index of the first "new" job
            # define newJobs to be all jobs in the range of mostRecentJob to the end of jobs



    def parseJobPage(self, response):

        jobPage = response.css("main section div")

        card = jobPage.css("section")[1].css("div div div")
        description = jobPage.css("div")

        
        # card has role, company, location, time posted, numApplicants, apply / save hrefs.
        role = card.css("h1::text").get().strip()
        company = card.css("h4 div a::text").get().strip()
        location = card.css("h4 div span::text").get().strip()
        timePosted = card.css("h4 div span::text")
