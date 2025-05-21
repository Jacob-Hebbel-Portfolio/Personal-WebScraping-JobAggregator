# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re

class JobscraperPipeline:
    def process_item(self, item, spider):
        

        # set which fields should be lowercase here
        fieldsToBeLowercase = ['company', 'employment', 'fields', 'industries', 'level',
                               'location', 'title', 'timePosted']
        
        for field in fieldsToBeLowercase:
            var = item[field] 

            # applies lowercase to strings and lists successfully
            item[field] = [v.lowercase() for v in var] if var is [] else var.lowercase()
        
       
        # parses the number from the applicants field
        regex = r"[0-9]"
        var = re.findall(item['numApplicants'], regex)
        item['numApplicants'] = var[0] if var != [] else None



        # populates the currency field
        # uses heuristic: if not provided assume $
        # easily add a currency option by appending to the regex
        regex = r"\$|£|€|₹|¥"
        var = re.findall(item['salary'], regex)[0]
        item['currency'] = var[0] if var != [] else '$'



        # turns salary into a 'range' with 2 indices, representing the low and high of the range
        regex = r"\d{1,3}(,\d{3})*(\.[0-9]+)?"
        var = re.findall(item['salary'], regex)

        if var == []:
            # no match found
            pass
        
        elif len(var) == 1:
            # 1 match found ==> 1 number
            var = var[0].replace(',', '')
            item['salary'] = [float(var), float(var)]

        elif len(var) == 2:
            # 2 matches found ==> true range
            var = [v.replace(',', '') for v in var]
            item['salary'] = sorted([float(v) for v in var])

        else:
            # undefined behavior occurring; should throw exception?
            pass

        
        
        # standardizing timePosted in hours (as a float)
        conversions = {'second': 1/(60*60), 'seconds': 1/(60*60), 'minute': 1/60, 'minutes': 1/60, 
                       'hour': 1, 'hours': 1, 'day': 24, 'days': 24, 
                       'week': 7*24, 'weeks': 7*24, 'month': 30*24, 'months': 30*24, 'year': 365*24, 'years': 365*24}
        
        var = item['timePosted'].split(" ")
        
        if len(var) != 3:
            # undefined behavior, just put the number in there??
            regex = r'/d'
            var = re.findall(item['timePosted'], regex)
            item['timePosted'] = float(var[0]) if var != [] else None

        else:
            number = var[0].strip()
            unit = var[1].strip()

            # completes the conversion if the unit is in there. else it just puts the number in
            item['timePosted'] = (float(number) * conversions[unit]) if unit in conversions.keys() else float(number)
                

        return item
    
