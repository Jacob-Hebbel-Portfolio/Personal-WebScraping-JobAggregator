# Scrapy settings for jobscraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "jobscraper"

SPIDER_MODULES = ["jobscraper.spiders"]
NEWSPIDER_MODULE = "jobscraper.spiders"
OUTPUT_FILE_PATH = '../output/output.jl'
FEEDS = {
    OUTPUT_FILE_PATH: {
        'format': 'jsonlines',
        'encoding': 'utf-8',
        'store-empty': False
    }
}
#LOG_FILE = "../output/output.log"
LOG_LEVEL = 'INFO'
ADDONS = {}

# Selenium Settings
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = ''
SELENIUM_DRIVER_ARGUMENTS = ['--headless=new']
SELENIUM_BROWSER_EXECUTABLE_PATH = ''

#SELENIUM_DRIVER_NAME = 'chrome'
#SELENIUM_DRIVER_EXECUTABLE_PATH = r'C:\Users\jacob\harp\projects\portfolio\job-posting-aggregator\chromedriver-win64\chromedriver.exe'
#SELENIUM_DRIVER_ARGUMENTS = ['--headless']

# Rotating Proxy Settings
#ROTATING_PROXY_LIST_PATH = '../data/proxies.txt'

#ROTATING_PROXY_PAGE_RETRY_TIMES = 10
# settings for randomizing request frequency
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "jobscraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "jobscraper.middlewares.JobscraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'jobscraper.middlewares.ScrapeOpsFakeBrowserHeaderAgentMiddleware': 400,
    #'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    #'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
    'jobscraper.middlewares.SeleniumUndetectedDownloaderMiddleware': 800,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}


# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "jobscraper.pipelines.JobscraperPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
CONCURRENT_REQUESTS_PER_DOMAIN = 1
AUTOTHROTTLE_ENABLED = False
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
