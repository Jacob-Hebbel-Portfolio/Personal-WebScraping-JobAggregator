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

        for header in headers_to_fake:
            request.headers[header] = fake_headers[header]

        print("*"*25 + "NEW HEADERS ATTACHED" + "*"*25)
        print(request.headers)



from scrapy_selenium.middlewares import SeleniumMiddleware
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

class ProxySeleniumMiddleware(SeleniumMiddleware):

    def _get_driver(self, request):
        
        # prevents window from opening every time I crawl
        driverOptions = Options()
        #driverOptions.add_argument("--headless=new")  

        # assigns the proxy from the rotating proxy list setting
        proxy = request.meta.get('proxy')
        if proxy:
            driverOptions.add_argument(f"--proxy-server={proxy}")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=driverOptions)
        return driver