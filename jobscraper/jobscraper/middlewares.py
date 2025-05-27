# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


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
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, ElementClickInterceptedException, TimeoutException

# misc imports
from util import DriverPool
from scrapy.http import HtmlResponse
from urllib.parse import urlparse
from random import randint
from scrapy import signals


'''
This middleware interacts with the browser page to generate dynamic content. This is done via a webdriver (undetectable chrome)
that observes the state of page content. It waits for the content to load then interacts with it, or observes an implicit wait signal.
'''
class SeleniumUndetectedDownloaderMiddleware:

    def __init__(self):

        # driver pool instance to access web drivers
        self.drivers = DriverPool()

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()              # frees drivers on SIGINT
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    # dictates webdriver behavior
    def process_request(self, request, spider):
        
        # gets the web driver
        webDriver = self.drivers.getDriver(request)
        webDriver.get(request.url)
        spider.logger.info(f"Middleware:\tprocessing request to {request.url}")
        webDriver.implicitly_wait(randint(1,5))

        # determines what action to do
        path = urlparse(request.url).path
        if 'search' in path:
            spider.logger.debug(f"Middleware:\texecuting job search logic")
            self.loadSearchResults(webDriver, spider)
        
        elif 'view' in path:
            spider.logger.debug(f"Middleware:\texecuting job view logic")
            wait = WebDriverWait(webDriver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'num-applicants__caption')]")))

        elif 'authwall' in path:
            spider.logger.error(f"Middleware:\tauthwall encountered")

        # responds with html page that has all the needed dynamic content
        spider.logger.debug(f"Middleware:\treturning fully-loaded page")
        spider.logger.debug(webDriver.page_source[:1000])
        
        url = webDriver.current_url
        page = webDriver.page_source

        return HtmlResponse(
            url=url,
            body=page,
            request=request,
            encoding='utf-8'
        )
    
    def loadSearchResults(self, webDriver, spider):

        loadedAllContent = False                                    # tells webdriver when to stop loading page
        actionCount = 0                                             # curtails posisble inf behavior
        
        while loadedAllContent == False and actionCount < 5:       # loop until no more content to generate
            #spider.logger.info('attempting content generation action')
            # button is present ==> button may be interactable
            # IF INTERACTABLE: click button to generate new content
            # IF !INTERACTABLE: scroll to generate new content
            # IF !PRESENT: return page
            try:
                # attempt generating content by finding & clicking button; this shouldn't work for a bit
                button = webDriver.find_element(By.XPATH, "//button[contains(@class, '__show-more-button')]")
                button.click()
                webDriver.implicitly_wait(randint(1,5))
                #spider.logger.info('successfully clicked button')
                actionCount+=1
            
            # attempts other ways of clicking the button
            except ElementClickInterceptedException:
                webDriver.implicitly_wait(randint(2,7))
                
                try:        # clicking with selenium
                    WebDriverWait(webDriver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "__show-more-button")]'))
                    )
                    button = webDriver.find_element(By.XPATH, '//button[contains(@class, "__show-more-button")]')
                    button.click()
                    #spider.logger.info('waited until overlay disappeared then clicked')
                    actionCount +=1

                            # clicking with javascript (this one usually works over the other)
                except (ElementClickInterceptedException, TimeoutException):
                    button = webDriver.find_element(By.XPATH, '//button[contains(@class, "__show-more-button")]')
                    webDriver.execute_script('arguments[0].click();', button)
                    #spider.logger.info('clicked button with javascript')
                    actionCount+=1

            # attempts scrolling to make more content
            except ElementNotInteractableException:
                # button is not interactable ==> do scroll action / location pair to generate content
                #spider.logger.info(f'no button found; doing scroll number {actionCount} instead')
                webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                webDriver.implicitly_wait(randint(1,5))
                actionCount+=1

            except NoSuchElementException:
                # button is not present ==> no more content to generate
                spider.logger.info("cannot make more content; returning page")
                loadedAllContent = True
                
        
        if loadedAllContent:
            spider.logger.info(f"Middleware:\tleaving loadSearchResults after loading all possible jobs")
        
        elif actionCount == 5:
            spider.logger.info(f"Middleware:\tleaving loadSearchResults after 5 actions")

        else:
            spider.logger.warning("Middleware:\tleaving search results and I don't know why ......")

    # frees drivers via .deleteDrivers()
    def spider_closed(self, spider):
        self.drivers.deleteDrivers()
        spider.logger.info("Middleware:\tall selenium drivers successfully closed.")