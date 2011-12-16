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

import urllib
import datetime
from time import time

import config
import web
from web import form

urls = (
'/', 'index',
'/top', 'top',
'/about', 'about',
'/([a-z]*)/([0-9]{6})/(.*)', 'result',
'/.*', 'notfound'
)

app = web.application(urls, globals())

LATESTTOP = "201012"

PROJECTS = [("English","en"),
            ("German","de"),
            ("French","fr"),
            ("Polish","pl"),
            ("Japanese","ja"),
            ("Italian","it"),
            ("Dutch","nl"),
            ("Portuguese","pt"),
            ("Spanish","es"),
            ("Swedish","sv"),
            ("Russian","ru"),
            ("Chinese","zh"),
            ("Chinese (classical)","zh-classical"),
            ("Norwegian","no"),
            ("Finnish","fi"),
            ("Volapük","vo"),
            ("Catalan","ca"),
            ("Romanian","ro"),
            ("Turkish","tr"),
            ("Ukrainian","uk"),
            ("Esperanto","eo"),
            ("Czech","cs"),
            ("Hungarian","hu"),
            ("Slovak","sk"),
            ("Danish","da"),
            ("Indonesian","id"),
            ("Hebrew","he"),
            ("Lithuanian","lt"),
            ("Serbian","sr"),
            ("Slovenian","sl"),
            ("Arabic","ar"),
            ("Korean","ko"),
            ("Bulgarian","bg"),
            ("Estonian","et"),
            ("Newar / Nepal Bhasa","new"),
            ("Croatian","hr"),
            ("Telugu","te"),
            ("Cebuano","ceb"),
            ("Galician","gl"),
            ("Thai","th"),
            ("Greek","el"),
            ("Persian","fa"),
            ("Vietnamese","vi"),
            ("Norwegian (Nynorsk)","nn"),
            ("Malay","ms"),
            ("Simple English","simple"),
            ("Basque","eu"),
            ("Bishnupriya Manipuri","bpy"),
            ("Bosnian","bs"),
            ("Luxembourgish","lb"),
            ("Georgian","ka"),
            ("Icelandic","is"),
            ("Albanian","sq"),
            ("Breton","br"),
            ("Latin","la"),
            ("Azeri","az"),
            ("Bengali","bn"),
            ("Hindi","hi"),
            ("Marathi","mr"),
            ("Tagalog","tl"),
            ("Macedonian","mk"),
            ("Serbo-Croatian","sh"),
            ("Ido","io"),
            ("Welsh","cy"),
            ("Piedmontese","pms"),
            ("Sundanese","su"),
            ("Latvian","lv"),
            ("Tamil","ta"),
            ("Neapolitan","nap"),
            ("Javanese","jv"),
            ("Haitian","ht"),
            ("Low Saxon","nds"),
            ("Sicilian","scn"),
            ("Occitan","oc"),
            ("Asturian","ast"),
            ("Kurdish","ku"),
            ("Armenian", "hy"),
            ("Commons","commons.m"),
            ("Meta","meta.m")]

PROJECTS = [(key, value) for value, key in PROJECTS]

class base(object):
    def __init__(self, *args, **kwargs):
        super(base, self).__init__(*args, **kwargs)
        self.db = web.database(dbn='mysql', host= config.db_host, user= config.db_user , pw=config.db_password, db='wikistats')

class notfound:
    def GET(self):
        return web.notfound()


class about:
    def GET(self):
        render = web.template.render('templates/')
        return render.about()

class top(base):
    def GET(self):
        proj = 'en' #Add code to parse out proj from URL.
        rows = self.db.query("SELECT rank,project,page,hitcount FROM top_%s WHERE project='%s' ORDER BY RANK LIMIT 1000" % (LATESTTOP, proj))
        render = web.template.render('templates/')
        return render.top(rows, LATESTTOP)

class index(base):
    def init_form(self, prevform=None):
        years, latest = getdates()
        if not prevform:
            search = form.Form(
            form.Dropdown('proj', PROJECTS, value=latest, description=''),
            form.Dropdown('year', years, description=''),
            form.Textbox('inputbox',form.notnull,id='ib1', description=''),
            form.Button('Top'))
        else:
            search = form.Form(
            form.Dropdown('proj', PROJECTS, value=prevform['proj'], description=''),
            form.Dropdown('year', years, value=prevform['year'], description=''),
            form.Textbox('inputbox', form.notnull,value=prevform['inputbox'],id='ib1', description=''),
            form.Button('Top'))
        return search
    
    def GET(self):
        form =  self.init_form()
        render = web.template.render('templates/', base='index')
        return render.form(form)
        
    def POST(self): 
        search = web.input()       
        return web.redirect('/%s/%s/%s' % (search['proj'], search['year'], search['inputbox']))
    
  

class result(base): 
    def GET(self,proj=None, year=None, page=None):
        render = web.template.render('templates/', base='index')
        search =dict(proj=proj, year=year, inputbox=page)
        idx =index()
        form =  idx.init_form(search)

        
        if not form.validates(form):
            return render.form(form)
        elif self.block_scraper()==True:
            return render.blocked()
        else:
            counts, maxcount, rank, date, dt = self.fetch_results(search)
            total_hits_html = self.results_overview(counts, search['proj'], rank, date, search['inputbox'])
            #print counts, maxcount, total_hits_html, dt, form
            return render.results(counts, maxcount, total_hits_html, dt, form)

    def block_scraper(self):
        scrapers = {'147.46.178.146':True,
                    '63.196.132.64':True,
                    '129.110.5.91':True}
        return scrapers.get(web.ctx['ip'],False)
        
    
    def results_overview(self, counts, proj, rank, date, page):
        cvt = { "commons.m" : "commons.wikimedia.org",
               "en.n" : "en.wikinews.org",
               "sv.s" : "sv.wikisource.org"}
        try:
            proj = cvt[proj]
        except KeyError:
            proj = proj + ".wikipedia.org"
    
        total = sum(counts)
        total_hits_html ='<p><a href="http://%s/wiki/%s">%s</a> has been viewed' % (proj, urllib.quote_plus(page), page)
        if date == -1:
            total_hits_html = '%s %s times in the last 30 days.' % (total_hits_html, total)
        else:
            total_hits_html ='%s %s times in %s.' % (total_hits_html, total ,date) 
        
        if rank.c > 0:
            total_hits_html = '%s This article ranked %s in traffic on %s.' % (total_hits_html, rank,proj)
        
        return total_hits_html
    
    def fetch_results(self, search):
        start = time()
        today = datetime.date.today()
        page = search['inputbox']
        date = search['year']
        proj = search['proj']
    
        days = range(1,32)
        page = urllib.unquote(page).strip().replace(" ","_")
        
        if date == -1:
            startd=today-datetime.timedelta(days=30)
            ix = startd
            for i in range(0,31):
                days[i] = ix.day
                ix += datetime.timedelta(days=1)
            months = getdates((startd.year, startd.month))[0]
            counts = []
            for m in months:
                try:
                    counts.extend(getcounts_new(self.db,m,proj,page).values())
                except:
                    counts.extend(getcounts(self.db,m,proj,page).values())
            counts = counts[-30:]
    
        else:
            try:
                counts = getcounts_new(self.db,date,proj,page).values()
            except:
                counts = getcounts(self.db,date,proj,page).values()
    
        try:
            maxcount = float(max(counts))
        except:
            maxcount = 1
    
        if maxcount == 0:
            maxcount = 1
    
        rank = self.db.query("SELECT rank FROM top_%s WHERE project='%s' AND page='%s'" % (LATESTTOP,proj,page))
        #print 'RANK: %s' % dir(rank), rank.c, rank.i
#        try:
#            rank = c.fetchone()[0]
#        except:
#            rank = -1
            
        end = time()
        dt = end-start
        return counts, maxcount, rank, date, dt


def getdates(start = None):
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

def getalldays(c,date):
    rows = c.query("SHOW TABLES like 'pagecounts_%s__';" % date)
    #c.execute("SHOW TABLES like 'pagecounts_%s__';" % date)
    #rows = c.fetchall()
    all_days = [x.values()[0] for x in rows]
    return all_days

def getalldays_new(c,date):
    #c.execute("SHOW TABLES like 'pagecounts_%s';" % date)
    rows =c.query("SHOW TABLES like 'pagecounts_%s';" % date)
    #rows = c.fetchall()
    all_days = [x.values()[0] for x in rows]
    return all_days


def getcounts(c,date,proj,page):
    all_days = getalldays(c,date)
    counts = {}
    for day in all_days:
        count = c.query("SELECT sum(hitcount) FROM "+day+" WHERE page=$page AND project=$project;", vars = {'page' : page, 'project' : proj })
        #c.execute("SELECT sum(hitcount) FROM "+day+" WHERE page=%s AND project=%s;", (page,proj))
        #count = c.fetchone()[0]
        day = int(day.split("_")[1][-2:])
        #print dir(count)
        try:
            counts[day] = int(count[0].values()[0])
        except TypeError:
            counts[day] = 0

    return counts

def getcounts_new(c,date,proj,page):

    tables = getalldays_new(c,date)
    counts = {}
    for i in range(0,32):
        counts[i]=0

    if len(tables) != 1:
        raise "Not in new format"

    table = tables[0]

    #c.execute("SELECT sum(hitcount),sum(d1), sum(d2), sum(d3), sum(d4), sum(d5), sum(d6), sum(d7), sum(d8), sum(d9), sum(d10), sum(d11), sum(d12), sum(d13), sum(d14), sum(d15), sum(d16), sum(d17), sum(d18), sum(d19), sum(d20), sum(d21), sum(d22), sum(d23), sum(d24), sum(d25), sum(d26), sum(d27), sum(d28), sum(d29), sum(d30), sum(d31) FROM "+table+" WHERE page=%s AND project=%s;", (page,proj))
    count = c.query("SELECT sum(hitcount),sum(d1), sum(d2), sum(d3), sum(d4), sum(d5), sum(d6), sum(d7), sum(d8), sum(d9), sum(d10), sum(d11), sum(d12), sum(d13), sum(d14), sum(d15), sum(d16), sum(d17), sum(d18), sum(d19), sum(d20), sum(d21), sum(d22), sum(d23), sum(d24), sum(d25), sum(d26), sum(d27), sum(d28), sum(d29), sum(d30), sum(d31) FROM "+table+" WHERE page=%s AND project=%s;", (page,proj))
    #count = c.fetchone()

    # One time bug in the database generation script
    # caused this months dates to be offset for one
    # day.
    if date == "200806":
        i = 0
    else:
        i = 1

    for x in count[1:]:
        counts[i]=int(x)
        i=i+1

    return counts

if __name__ == '__main__':
    if config.DEBUG:
        app.run()
    
