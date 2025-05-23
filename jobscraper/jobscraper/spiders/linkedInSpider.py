import scrapy
from jobscraper.items import JobItem

# misc
import re
from util import loadDataFile
from util import getSalary
from util import LinkedInValidator


class LinkedinspiderSpider(scrapy.Spider):
    name = "linkedInSpider"
    allowed_domains = ["www.linkedin.com"]

    # ========== spider entry ==========
    def start_requests(self):
        
        # get search args
        keywords = loadDataFile('keywords.txt')
        locations = loadDataFile('locations.txt')

        # loops over all args
        for location in locations:
            for keyword in keywords:
                
                # building url
                root = "https://www.linkedin.com/jobs/search"
                url = f"{root}?keywords={keyword}&location={location}"
                self.logger.info(f"\n\nvisiting {url}\n\n")
                
                # sending request
                yield scrapy.Request(
                    url=url,
                    callback=self.parseSearch
                )


    def parseSearch(self, response):
        

        # ========== getting & debugging jobs ========== 

        jobs = response.css("ul[class*='jobs-search__results-list'] li")

        if len(jobs) == 0:
            self.logger.warning(f"no jobs found at: {response.url}")
            self.logger.warning(response.css("*").get()[:500])
            return
        else:
            self.logger.info(f"successfully scraped {len(jobs)} job(s) from {response.url}")
        for job in jobs:
            jobLink = job.css('a::attr(href)').get()


            # ========== following link inside job ========== 

            if jobLink is not None:
                yield response.follow(jobLink.strip().split('?')[0])
            else:
                self.logger.warning(f"could not find job page from {response.url}")


    def parseJob(self, response):
       
        self.logger.info(f"reached page: {response.url}")
        self.logger.info(f"starting parsing process. page preview:\n{response.css('*').get()[:500] if response.css('*').get() is not None else 'No page content available'}")


        # ========== error checking ==========

        if LinkedInValidator.validates(response, self.logger):
            pass
        else:
            return
        

        # ========== url, id, and page parsing ========== 

        # parsing id & url
        regex = r"\d+"
        rootURL = response.url.split('?')[0]
        matches = re.findall(regex, rootURL)

        # skips if id is missing
        if matches == []:
            self.logger.warning(f"Could not extract job ID from URL: {response.url}")
            self.logger.info(f"skipping url: {response.url}")
            return
        
        id = sorted(matches)[-1]        # heuristic: id is usually long, assume it is the longest matching number
        url = f"https://linkedin.com/jobs/view/{id}"


        # splitting page
        card = response.css("div[class*='info']")[1]
        description = response.css("div[class*='posting__details']")
        

        # ========== parsing card ==========

        # card has title, company, location, time posted, numApplicants, apply / save hrefs.
        title = card.css("h1[class*='title']::text").get().strip()
        company = card.css("a[class*='org-name']::text").get().strip()
        location = card.css("span[class*='bullet']::text").get().strip()
        timePosted = card.css("span[class*='posted-time']::text").get().strip()
        numApplicants = response.xpath("//*[contains(@class, 'num-applicants__caption')]/text()").get().strip()


        # ========== parsing description ==========
        
        # criteria gets area, level, employment, and industries
        criteria = description.css("ul[class*='criteria'] li")

        level = criteria[0].css('span::text').get().strip()
        employment = criteria[1].css('span::text').get().strip()
        
        
        # choosing to format fields & industries as lists of keywords
        l = criteria[2].css('span::text').get().strip().split(", ")
        s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
        l.pop()
        fields = [keyword.strip() for keyword in l + s 
                  if keyword is not None 
                  and keyword.strip() != '']

        l = criteria[3].css('span::text').get().strip().split(", ")
        s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
        l.pop()
        industries = [keyword.strip() for keyword in l + s 
                  if keyword is not None 
                  and keyword.strip() != '']

        salary = getSalary(description)


        # ========== item assignment ==========

        job = JobItem()

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
        
        yield job

        self.logger.info(f"\n\n\nScraped job: {job['title']} at {job['company']} for {job['salary'] if job['salary'] != None else 'None'}\n\n\n")