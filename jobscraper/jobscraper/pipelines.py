# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re

class JobscraperPipeline:

    # formats items to be ready for insertion into a db
    def process_item(self, item, spider):

        # set which fields should be lowercase here
        fieldsToBeLowercase = ['company', 'employment', 'fields', 'industries', 'level',
                               'location', 'title', 'timePosted']
        
        for field in fieldsToBeLowercase:
            
            var = item[field]
            if var is not None:
                if isinstance(var, list):
                    item[field] = [v.lower() for v in var if v is not None]
                elif isinstance(var, str):
                    item[field] = var.lower()
            else:
                item[field] = None
        
       
        # parses the number from the applicants field
        if item['numApplicants'] is not None:
            regex = r"\d+"
            matches = re.findall(regex, item['numApplicants'])
            item['numApplicants'] = matches[0] if matches != [] else None



        # populates the currency field
        # uses heuristic: if not provided assume $
        # easily add a currency option by appending to the regex
        if item['salary'] is not None:
            regex = r"\$|£|€|₹|¥"
            matches = re.findall(regex, item['salary'])
            item['currency'] = matches[0] if matches != [] else '$'


        

        # turns salary into a 'range' with 2 indices, representing the low and high of the range
        salary = item.get('salary')
        if salary is not None:

            matches = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.[0-9]+)?", salary)
            numbers = [float(m.replace(',', '')) for m in matches]

            if len(numbers) == 1:
                item['salary'] = [numbers[0], numbers[0]]
            elif len(numbers) == 2:
                item['salary'] = sorted(numbers)
            else:
                item['salary'] = None
                item['currency'] = None
        else:
            item['salary'] = None
            item['currency'] = None

        
        
        # standardizing timePosted in hours (as a float)
        conversions = {'second': 1/(60*60), 'seconds': 1/(60*60), 'minute': 1/60, 'minutes': 1/60, 
                       'hour': 1, 'hours': 1, 'day': 24, 'days': 24, 
                       'week': 7*24, 'weeks': 7*24, 'month': 30*24, 'months': 30*24, 'year': 365*24, 'years': 365*24}
        

        var = item['timePosted'].split(" ") if item['timePosted'] is not None else ['24', 'hours', 'ago']
        
        try:
            
            if len(var) == 3:
                # case of successful split
                number = float(var[0])
                unit = var[1].lower()
                item['timePosted'] = number * conversions.get(unit, 1.0) if unit in conversions.keys() else number
            else:
                # try extracting the number and assume it is in hours
                regex = r"\d+"
                matches = re.findall(regex, item['timePosted'])
                item['timePosted'] = matches[0] if matches != [] else 24.0

        except Exception as e:
            spider.logger.warning(f"Failed to convert timePosted: '{item['timePosted']}' - {e}")
            item['timePosted'] = 24.0
                

        return item
    
