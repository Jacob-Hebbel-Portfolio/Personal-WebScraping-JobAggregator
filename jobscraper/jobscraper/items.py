# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class JobscraperItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class JobItem(Item):
    
    url = Field()
    title = Field()
    level = Field()
    fields = Field()
    salary = Field()
    company = Field()
    location = Field()
    currency = Field()
    industries = Field()
    employment = Field()
    timePosted = Field()
    scrapedFrom = Field()
    numApplicants = Field()
    
    
    
