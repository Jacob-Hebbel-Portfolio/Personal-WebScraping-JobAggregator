import requests
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from jobscraper.spiders.linkedInSpider import LinkedinspiderSpider

import os
import requests

def get_proxies():
    url = "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt"
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch proxies: {response.status_code}")

    proxies = [line.strip() for line in response.text.strip().splitlines() if line.strip()]
    return proxies


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define full path to output file
output_file_path = os.path.join(OUTPUT_DIR, 'output.jl')

# Remove old file if it exists
if os.path.exists(output_file_path):
    os.remove(output_file_path)

settings = get_project_settings()
settings.set('ROTATING_PROXY_LIST', get_proxies())
settings.set('FEEDS', {
    output_file_path: {
        'format': 'jsonlines',
        'encoding': 'utf-8',
        'store-empty': False
    }
})


process = CrawlerProcess(settings)
process.crawl(LinkedinspiderSpider)
process.start()