# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

class JobscraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class JobscraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)



import requests
from random import randint
from urllib.parse import urlencode

class ScrapeOpsFakeBrowserHeaderAgentMiddleware:
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def __init__(self, settings):
        self.scrapeops_api_key = settings.get("SCRAPEOPS_API_KEY")
        self.scrapeops_endpoint = settings.get("SCRAPEOPS_FAKE_BROWSER_HEADER_ENDPOINT", "https://headers.scrapeops.io/v1/browser-headers")
        self.scrapeops_fake_browser_headers_active = settings.get("SCRAPEOPS_FAKE_BROWSER_HEADER_ENABLED", True)
        self.scrapeops_num_results = settings.get("SCRAPEOPS_NUM_RESULTS")
        self.headers_list = []
        self._get_headers_list()
        self._scrapeops_fake_browser_headers_enabled()

    def _get_headers_list(self):
        payload = {'api_key': self.scrapeops_api_key}
        if self.scrapeops_num_results is not None:
            payload['num_results'] = self.scrapeops_num_results
        
        response = requests.get(self.scrapeops_endpoint, params=urlencode(payload))
        jsonResponse = response.json()

        self.headers_list = jsonResponse.get('result', [])

        headers_to_fake = ['accept-language', 'sec-fetch-user', 'sec-fetch-mode', 'sec-fetch-site',
                   'sec-ch-ua-platform', 'sec-ch-ua-mobile', 'sec-ch-ua', 'accept', 'user-agent',
                   'upgrade-insecure-requests']
        
        self.headers_list = [
            fake_headers for fake_headers in self.headers_list
            if all(header in fake_headers.keys() for header in headers_to_fake)
        ]

    
    def _get_random_browser_header(self):
        
        randomIndex = randint(0, len(self.headers_list) - 1)
        return self.headers_list[randomIndex]
    

    def _scrapeops_fake_browser_headers_enabled(self):

        if self.scrapeops_api_key is None or self.scrapeops_api_key == '' or self.scrapeops_fake_browser_headers_active == False:
            self.scrapeops_fake_browser_headers_active = False
        else:
            self.scrapeops_fake_browser_headers_active = True

    
    def process_request(self, request, spider):
        fake_headers = self._get_random_browser_header()

        headers_to_fake = ['accept-language', 'sec-fetch-user', 'sec-fetch-mode', 'sec-fetch-site',
                   'sec-ch-ua-platform', 'sec-ch-ua-mobile', 'sec-ch-ua', 'accept', 'user-agent', 
                   'upgrade-insecure-requests']

        request.meta['fake_browser_headers'] = { str(k): str(v) for k, v in fake_headers.items() }

        #print("*"*25 + "NEW HEADERS ATTACHED" + "*"*25)
        #print(request.headers)


# logic & loading imports
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException

# misc imports
from util import DriverPool
from scrapy.http import HtmlResponse
from urllib.parse import urlparse
from random import randint
from scrapy import signals


class SeleniumUndetectedDownloaderMiddleware:

    def __init__(self):

        self.drivers = DriverPool()

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()              # frees drivers on SIGINT
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    # executes webdriver behavior here 
    def process_request(self, request, spider):
        
        # gets the web driver
        webDriver = self.drivers.getDriver(request)
        webDriver.get(request.url)
        spider.logger.info(f"\n\nprocessing request to {request.url}\n\n")

        # determines what action to do
        path = urlparse(request.url).path
        if 'search' in path:
            spider.logger.info(f"\n\nexecuting job search logic\n\n")
            self.loadSearchResults(webDriver, spider)
        
        elif 'view' in path:
            spider.logger.info(f"\n\nexecuting job view logic\n\n")
            wait = WebDriverWait(webDriver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'num-applicants__caption')]")))

        # responds with html page that has all the needed dynamic content
        spider.logger.info(f"\n\nreturning fully-loaded page\n\n")
        spider.logger.info()
        return HtmlResponse(
            url=webDriver.current_url,
            body=webDriver.page_source,
            request=request,
            encoding='utf-8'
        )
    
    def loadSearchResults(self, webDriver, spider):

        loadedAllContent = False                                    # turns True to tell webdriver to stop trying
        scrollCount = 0                                             # curtails posisble inf behavior
        
        while loadedAllContent == False and scrollCount <= 25:      # loop until no more content to generate

            try:
                spider.logger.info('attempting to click the button')

                # button is present ==> button may be interactable
                # IF INTERACTABLE: click button to generate new content
                # IF !INTERACTABLE: scroll to generate new content
                # IF !PRESENT: kill process 
                button = webDriver.find_element(By.XPATH, "//button[contains(@class, '__show-more-button')]")
                button.click()
                webDriver.implicitly_wait(randint(2,5))

            except ElementNotInteractableException:
                # button is not interactable ==> do scroll action / location pair
                spider.logger.info(f'no button found; doing scroll number {scrollCount} instead')
                
                loadedAllContent = True

            except NoSuchElementException:
                spider.logger.info("cannot make more content; returning page")
                

                # button is not present ==> scrolling makes more jobs appear
                webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                webDriver.implicitly_wait(randint(2,5))
                scrollCount+=1

            if loadedAllContent:
                spider.logger.info(f"leaving loadSearchResults after loading all possible jobs")
            
            elif scrollCount > 25:
                spider.logger.info(f"leaving loadSearchResults after scrolling too much :(((")

            else:
                spider.logger.warn("attempting to generate more content")

    # frees drivers via .deleteDrivers()
    def spider_closed(self, spider):
        self.drivers.deleteDrivers()
        spider.logger.info("all selenium drivers successfully closed.")