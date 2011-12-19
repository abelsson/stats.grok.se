# -*- coding: utf-8 -*-
#  Copyright (C) 2011 Henrik Abelsson <henrik@grok.se>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime, time
import web
import config


class OldFormatException(Exception):
    def __init__(self, value = "Old format"):
        self.value = value

        def __str__(self):
            return repr(self.value)

db = web.database(dbn='mysql', host=config.db_host, user= config.db_user , pw=config.db_password, db='wikistats', charset=None)




def get_dates(start = None):
    if start == None:
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


def get_top(proj):
    return db.query("SELECT rank,project,page,hitcount FROM top_%s WHERE project='%s' ORDER BY RANK LIMIT 1000" % (config.LATESTTOP, proj))
            
def get_rank(page,  proj):
    rank = db.query("SELECT rank FROM top_%s WHERE project='%s' AND page='%s'" % (config.LATESTTOP,proj,page))
    try:
        return rank[0].rank
    except IndexError:
        return -1

def get_latest_stats(page, proj):
    ''' Fetch statistics in a list of view counts, for the latest 30 days '''
    start = time.time()
    
    days = range(1,32)
    today = datetime.date.today()
        
    startd=today-datetime.timedelta(days=30)
    ix = startd
    for i in range(0,31):
        days[i] = "%d-%02d-%02d" % (ix.year, ix.month, ix.day)
        ix += datetime.timedelta(days=1)
    months = get_dates((startd.year, startd.month))[0]
    page_counts = {}
    for m in months:
        try:
            page_counts = dict(page_counts.items() + _getcounts_new(db,m,proj,page).items())
        except:
            page_counts = dict(page_counts.items() + _getcounts(db,m,proj,page).items())


    for x in page_counts.keys():
        if not x in days:
            del page_counts[x]
    #page_counts = page_counts[-30:]
 
    end = time.time()
    execution_time = end-start
    return page_counts, execution_time

def get_monthly_stats(page, date, proj):
    ''' Fetch statistics as a list of view counts, for a given month'''
    start = time.time()

    try:
        page_counts = _getcounts_new(db,date,proj,page)
    except OldFormatException:
        page_counts = _getcounts(db,date,proj,page)   

    end = time.time()
    execution_time = end-start
    return page_counts, execution_time



def _getalldays(c,date):
    rows = c.query("SHOW TABLES like 'pagecounts_%s__';" % date)
    all_days = [x.values()[0] for x in rows]
    return all_days

def _getalldays_new(c,date):
    rows =c.query("SHOW TABLES like 'pagecounts_%s';" % date)
    all_days = [x.values()[0] for x in rows]
    return all_days


def _getcounts(c,date,proj,page):
    all_days = _getalldays(c,date)
    counts = {}
    for day in all_days:
        count = c.query("SELECT sum(hitcount) FROM "+day+" WHERE page=$page AND project=$project;", vars = {'page' : page, 'project' : proj })
        tmp = day.split("_")[1]
        year = tmp[0:4]
        month = tmp[4:6]
        day = tmp[6:]
        day = year + "-" + month + "-" + day
        try:
            counts[day] = int(count[0].values()[0])
        except TypeError:
            counts[day] = 0
            
    return counts

def _getcounts_new(c,date,proj,page):

    tables = _getalldays_new(c,date)

    counts = {}
    if len(tables) != 1:
        raise OldFormatException()

    table = tables[0]

    count = c.query("SELECT sum(hitcount),sum(d1), sum(d2), sum(d3), sum(d4), sum(d5), sum(d6), sum(d7), sum(d8), sum(d9), sum(d10), sum(d11), sum(d12), sum(d13), sum(d14), sum(d15), sum(d16), sum(d17), sum(d18), sum(d19), sum(d20), sum(d21), sum(d22), sum(d23), sum(d24), sum(d25), sum(d26), sum(d27), sum(d28), sum(d29), sum(d30), sum(d31) FROM "+table+" WHERE page=$page AND project=$project;", vars = {'page' : page.encode('utf-8'), 'project' : proj })

    # One time bug in the database generation script
    # caused this months dates to be offset for one
    # day.
    if date == "200806":
        fudge = 0
    else:
        fudge = 1

    values = count[0]
    year = date[0:4]
    month = date[4:6]
    for x in range(1,32):
        counts["%s-%s-%02d" % (year, month, x)]=int(values["sum(d%d)" % x])


    return counts

