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
    
    def get_top(self,proj):
        '''Return the x most viewed pages'''
        return
    
    def get_rank(self,page,  proj):
        return
    
    def get_latest_stats(self,page, proj):
        return
    
    def get_monthly_stats(self,page, date, proj):
        ''' Fetch statistics as a list of view counts, for a given month'''
        return

dm =DataModel()