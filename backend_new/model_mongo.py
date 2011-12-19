from abstract import AbstractDataModel

import datetime

class DataModel:

    def get_dates(self,start=None):    
        if not start:
            start = (2007, 12)
        today = datetime.date.today()
        end = (today.year, today.month)
        
        ret = []

#        x = start
#        
#        while x <= end:
#            year, month = x
#            ret.append("%d%02d" % (year, month))
#            month = month + 1
#            if month > 12:
#                month = 1
#                year = year + 1
#            x = (year, month)
#    
        latest = "%d%02d" % end
        return ret, latest

dm =DataModel()