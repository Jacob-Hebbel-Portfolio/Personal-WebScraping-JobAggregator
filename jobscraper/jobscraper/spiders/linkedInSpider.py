import scrapy
from jobscraper.items import JobItem

# misc
import re
from util import loadDataFile
from util import getSalary
from util import LinkedInValidator


class LinkedinspiderSpider(scrapy.Spider):
    name = "linkedInSpider"
    allowed_domains = ["linkedin.com"]

    # ========== spider entry ==========
    def start_requests(self):
        
        # get search args
        
        keywords = loadDataFile('keywords.txt')
        locations = loadDataFile('locations.txt')
        root = "https://www.linkedin.com/jobs/search"

        urls = [f"{root}?keywords={keyword}&location={location}" for keyword in keywords for location in locations]
        
        for url in urls:
            self.logger.info(f"[start_requests]:\tvisiting {url}")
                
            # sending request
            yield scrapy.Request(
                url=url,
                callback=self.parseSearch,
                meta={'source': 'search'}
            )
        
    def parse(self, response):


        # ========== routes to proper parsing function ==========

        self.logger.warning(f"Spider:\tFell into default parse method.\nURL: {response.url}")
        self.logger.info(f"Spider:\t[parse] response from {response.meta['source']} -> {response.url}")

        url = response.url

        if '/search' in url:
            self.logger.warning(f"Spider:\tNow routing to parseSearch")
            return self.parseSearch(response)
        else:
            self.logger.warning(f"Spider:\tNow routing to parseSearch")
            return self.parseJob(response)

    def parseSearch(self, response):
        
        self.logger.info("[parseSearch]:\treached parseSearch")
        self.logger.info(f"[parseSearch]:\t[parseSearch] response from {response.meta['source']} -> {response.url}")

        # ========== getting & debugging jobs ========== 

        jobs = response.css("ul[class*='jobs-search__results-list'] li")
        
        if len(jobs) == 0:
            self.logger.warning(f"[parseSearch]:\tno jobs found at: {response.url}")
            self.logger.warning(response.text[:500])
            return
        else:
            self.logger.debug(f"[parseSearch]:\t found {len(jobs)} job(s) from {response.url}")
        
        # making requests for every job
        jobLinks = []
        for job in jobs:
            jobLink = job.css('a::attr(href)').get()


            # ========== following link inside job ========== 

            if jobLink:
                self.logger.debug(f"[parseSearch]:\tfound a job: {jobLink.strip().split('?')[0]}")
                jobLinks.append(jobLink.strip().split('?')[0])
        
        for counter in range(5):
            yield response.follow(jobLinks[counter], callback=self.parseJob, meta={'source': 'search'})
        '''
        for job in jobs:
            jobLink = job.css('a::attr(href)').get()

            if jobLink:
                break
        
        self.logger.info(f"[parseSearch]:\tfollowing to {jobLink.strip().split('?')[0]}")
        yield response.follow(jobLink.strip().split('?')[0], callback=self.parseJob, meta={'source': 'search'})
        self.logger.info(f'[parseSearch]:\tcompleted follow')
        '''

    def parseJob(self, response):
       
        self.logger.info(f"[parseJob]:\treached page: {response.url}")
        self.logger.debug(f"[parseJob]:\tstarting parsing process. page preview:\n{response.text[:500]}")
        self.logger.info(f"[parseJob]:\t response from {response.meta['source']} -> {response.url}")

        # ========== error checking ==========

        if LinkedInValidator.validates(response, self.logger):
            pass
        else:
            self.logger.warning("[parseJob]:\tpage failed schema validation")
            return
        

        # ========== url, id, and page parsing ========== 

        # parsing id & url
        regex = r"\d+"
        rootURL = response.url.split('?')[0]
        matches = re.findall(regex, rootURL)

        self.logger.debug(f"[parseJob]:\tParsed root from {response.url}")
        self.logger.debug(f"[parseJob]:\tmatches= {matches}")
        # skips if id is missing
        if matches == []:
            self.logger.warning(f"[parseJob]:\tCould not extract job ID from URL: {response.url}")
            self.logger.debug(f"[parseJob]:\tskipping url: {response.url}")
            return
        
        id = sorted(matches, key=len)[-1]        # heuristic: id is usually long, assume it is the longest matching number
        url = f"https://linkedin.com/jobs/view/{id}"

        try:
            # splitting page
            card = response.css("div[class*='info']")[1]
            description = response.css("div[class*='posting__details']")

            self.logger.debug(f"[parseJob]:\tParsed card and root from {response.url}")
            self.logger.debug(f"[parseJob]:\t= {matches}")

        except Exception as e:
            self.logger.warning(f"[parseJob]:\terror when parsing card and description:")
            self.logger.warning(f"[parseJob]:\t{e}")
        # ========== parsing card ==========
        try: 
            # card has title, company, location, time posted, numApplicants, apply / save hrefs.
            title = card.css("h1[class*='title']::text").get(default='').strip()
            company = card.css("a[class*='org-name']::text").get(default='').strip()
            location = card.css("span[class*='bullet']::text").get(default='').strip()
            timePosted = card.css("span[class*='posted-time']::text").get(default='').strip()
            numApplicants = response.xpath("//*[contains(@class, 'num-applicants__caption')]/text()").get(default='').strip()

            self.logger.debug(f"[parseJob]:\tSuccessfully parsed information from card")
        except Exception as e:
            self.logger.warning(f"[parseJob]:\terror when parsing card info")
            self.logger.warning(f"{e}")


        # ========== parsing description ==========
        
        try:
            # criteria gets area, level, employment, and industries
            criteria = description.css("ul[class*='criteria'] li")

            level = criteria[0].css('span::text').get(default='').strip()
            employment = criteria[1].css('span::text').get(default='').strip()
            
            
            # choosing to format fields & industries as lists of keywords
            l = criteria[2].css('span::text').get(default='').strip().split(", ")
            s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
            l.pop()
            fields = [keyword.strip() for keyword in l + s 
                    if keyword is not None 
                    and keyword.strip() != '']

            l = criteria[3].css('span::text').get(default='').strip().split(", ")
            s = l[-1].split(" and ") if len(l) == 1 else l[-1].split("and ")
            l.pop()
            industries = [keyword.strip() for keyword in l + s 
                    if keyword is not None 
                    and keyword.strip() != '']

            salary = getSalary(description)

            self.logger.debug("[parseJob]:\tSuccessfully parsed description content")

        except Exception as e:
            self.logger.warning(f"[parseJob]:\terror when parsing description content")
            self.logger.warning(f"{e}")



        # ========== item assignment ==========
        try:
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
            
            self.logger.info(f"\n\n\nSpider:\tScraped job: |{job['title']}| at |{job['company']}| for |{job['salary']}|\n\n\n")
            yield job
        
        except Exception as e:
            self.logger.warning(f"Spider:\tthere was an error during item assignment: {e}")
        