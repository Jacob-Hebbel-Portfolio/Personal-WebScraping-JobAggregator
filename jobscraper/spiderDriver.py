from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from jobscraper.spiders.linkedInSpider import LinkedinspiderSpider

import signal
import sys

# kills process
def shutdownProcess(signum, frame):
    print("\nReceived interrupt. Shutting down...")
    stop_gracefully(process)
    sys.exit(0)



# starts the proxy service
settings = get_project_settings()


# listens for ctrl c (sigint)
signal.signal(signal.SIGINT, shutdownProcess)

process = CrawlerProcess(settings)
process.crawl(LinkedinspiderSpider)

# forces spider to close after receiving interrupt
try:
    process.start()
except KeyboardInterrupt:
    print("Manual interruption. Killing spider.")
    process.stop()
    sys.exit(0)