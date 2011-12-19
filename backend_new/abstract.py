
import datetime
from abc import ABCMeta, abstractmethod

class AbstractDataModel:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def get_dates(self,start = None):
        if not start:
            start = (2007, 12)
        today = datetime.date.today()
        end = (today.year, today.month)
    
        x = start
        ret = []
        while x <= end:
            year, month = x
            ret.append("%d%02d" % (year, month))
            month = month + 1
            if month > 12:
                month = 1
                year = year + 1
            x = (year, month)
    
        latest = "%d%02d" % end
        return ret, latest
    
    @abstractmethod
    def get_top(self,proj):
        return
    
    @abstractmethod    
    def get_rank(self,page,  proj):
        return
    
    @abstractmethod
    def get_latest_stats(self,page, proj):
        return
    
    @abstractmethod
    def get_monthly_stats(self,page, date, proj):
        ''' Fetch statistics as a list of view counts, for a given month'''
        return