# modify this to change how output data is stored
# make sure to update spiderDriver's feed arg if you change this
import os

def getOutputFilePath():
    dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(dir, exist_ok=True)
    path = os.path.join(dir, 'output.jl')
    return path



# used to read datafiles
import os
import urllib.parse

def loadDataFile(file):
    filePath = os.path.join(os.path.dirname(__file__), '..', 'data', file)
    with open(filePath, "r", encoding="utf-8") as f:
        return [urllib.parse.quote(line.strip()) for line in f if line.strip()]



# used in driver for fetching the list of proxies
# github link is refreshed ~5 mins with updated proxy info
# proxifly has lists for other protocols & us-based proxies
import requests

def getProxyList():
    url = "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt"
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch proxies: {response.status_code}")

    proxies = [line.strip() for line in response.text.strip().splitlines() if line.strip()]
    return proxies


def testProxy(proxy):

    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
    
    proxies = {
        "http": f"{proxy}",
        "https": f"{proxy}",
    }
    try:
        r = requests.get("https://www.linkedin.com", headers=headers, proxies=proxies, timeout=10)
        if r.status_code == 200 and "LinkedIn" in r.text:
            #print(f"found suitable proxy {proxy}")
            return True
    except:
        pass
    return False


def getXWorkingProxies(x):
    workingProxies = []
    proxies = getProxies()

    for proxy in proxies:
        
        if testProxy(proxy) == True:
            workingProxies.append(proxy)

            if len(workingProxies) % 10 == 0:
                print(f"{len(workingProxies)} working proxies")

            if len(workingProxies) >= x:
                return workingProxies
            
    return workingProxies


# parses the salary from a linkedIn description
import re

def getSalary(description):
    descAsString = " ".join(
                                [string.get().strip() 
                                for string in description.css("* *::text") 
                                if string.get() is not None
                                and string.get().strip() is not None]    )

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
    # this is no means perfect but rides the edge of excluding valid salaries at the expense of not collecting false data. This heuristic can be tweaked without error to the code
    regex = r"(?:\$|£|€|₹|¥)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*/\s*(?i:hr|hour|yr|year|mo|month))?(?:\s*(?:-|to)\s*(?:\$|£|€|₹|¥)?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*/\s*(?i:hr|hour|yr|year|mo|month))?)?"
    salaryMatches = sorted(re.findall(regex, descAsString), key=len) # heuristic: puts the longest match (most likely to be salary) at the back

    salary = salaryMatches[-1].strip() if salaryMatches != [] and len(salaryMatches[-1].strip()) > 8 else None

    return salary

import asyncio
import aiohttp

class ProxyPool:

    def __init__(self):
        self.allProxies = set(getProxyList())
        self.goodProxies = set()
        self.badProxies = set()
        self.session = None

    def isLow(self):
        return len(self.goodProxies) < 20 or len(self.badProxies) > 50

    async def startSession(self):
        self.session = aiohttp.ClientSession()

    async def closeSession(self):
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def getWorkingProxy(self):
        
        # returns a proxy from the goodProxy pool
        # refills the pool if it is low
        while len(self.goodProxies) < 10:
            count = min(20, len(self.allProxies) - 1, 0) if count > 0 else 0
            batch = [self.allProxies.pop() for _ in range(count)]
            await self.testProxies(batch)

        proxy = self.goodProxies.pop()
        return proxy

    
    async def testBadProxies(self):
        # takes the first 50 bad proxies and tests them
        count = min(50, len(self.badProxies) - 1, 0)  if count > 0 else 0
        batch = [self.badProxies.pop() for _ in range(count)]
        await self.testProxies(batch)

    async def validationTask(self, proxy):
        # benchmark task for determining if a proxy is good / bad

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

        try:
            async with self.session.get(
                "https://www.linkedin.com", 
                headers=headers, 
                proxy=f"http://{proxy}", 
                timeout=10
            ) as r:
                text = await r.text()
                if r.status == 200 and "LinkedIn" in text:
                    return True
        except:
            return False

    async def testProxies(self, batch):
        # aggregates which proxies to test and
        # runs the validation task for each asynchronously

        # collecting the tasks and executing them together
        tasks = [self.validationTask(proxy) for proxy in batch]
        results = await asyncio.gather(*tasks)

        # sorting the proxies based on their result
        for proxy, result in zip(batch, results):
            if result:
                self.goodProxies.add(proxy)
            else:
                self.badProxies.add(proxy)

    async def getInitialProxies(self):
        
        # keeps getting new proxies until there are at least 10
        while len(self.goodProxies) < 10:
            count = min(20, len(self.allProxies) - 1) if count > 0 else 0
            batch = [self.allProxies.pop() for _ in range(count)]
            await self.testProxies(batch)

        # returns 10 working proxies
        return [self.goodProxies.pop() for _ in range(count)]

PROXY_POOL = None
async def startProxyPool():
    global PROXY_POOL
    PROXY_POOL = ProxyPool()
    await PROXY_POOL.startSession()
    await PROXY_POOL.getInitialProxies()

# Run it synchronously before anything else uses PROXY_POOL
asyncio.run(startProxyPool())


import undetected_chromedriver as uc

class DriverPool:
    def __init__(self):
        self.pool = []

    def getDriver(self, request):
        proxy = request.meta.get('proxy', {})
        headers = request.meta.get('fake_browser_headers', {})
        userAgent = headers.get('user-agent', None)

        for driver in self.pool:
            if driver.proxy == proxy and driver.user_agent == userAgent:
                return driver

        newDriver = self.makeDriver(proxy, userAgent)
        self.pool.append(newDriver)
        return newDriver

    def makeDriver(self, proxy, userAgent):
        chromeOptions = uc.ChromeOptions()
        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--disable-blink-features=AutomationControlled")
        chromeOptions.add_argument("--ignore-certificate-errors")
        chromeOptions.add_argument("--no-sandbox")

        if proxy:
            chromeOptions.add_argument(f"--proxy-server={proxy}")

        if userAgent:
            chromeOptions.add_argument(f"--user-agent={userAgent}")

        driver = uc.Chrome(options=chromeOptions)

        driver.proxy = proxy
        driver.user_agent = userAgent

        return driver

    def deleteDrivers(self):
        for driver in self.pool:
            try:
                driver.quit()
            except:
                pass
        self.pool = []


class LinkedInValidator:
    
    @staticmethod
    def itIsAuthed(response):
        return 'login' in response.url or 'auth' in response.url

    @staticmethod
    def itIsClosed(response):
        return response.css("figure[class*='closed']").get() is not None

    @staticmethod
    def cardIsMissing(response):
        return response.css("div[class*='info']").get() is None

    @staticmethod
    def cardIsMalformed(response):
        return len(response.css("div[class*='info']").get()) < 2

    @staticmethod
    def descIsMissing(response):
        return response.css("div[class*='posting__details']").get() is None

    @staticmethod
    def descIsMalformed(response):
        return len(response.css("div[class*='posting__details'] ul[class*='criteria'] li").get()) < 4

    @classmethod
    def validates(cls, response, logger):
        if cls.itIsAuthed(response):
            logger.info("Login/auth wall encountered.")
            return False
        if cls.itIsClosed(response):
            logger.info("Job is closed.")
            return False
        if cls.cardIsMissing(response):
            logger.info("Job card missing.")
            return False
        if cls.cardIsMalformed(response):
            logger.info("Job card malformed.")
            return False
        if cls.descIsMissing(response):
            logger.info("Job description missing.")
            return False
        if cls.descIsMalformed(response):
            logger.info("Job description malformed.")
            return False
        return True