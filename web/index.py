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
import model

urls = (
'/', 'index',
'/about', 'about',
'/([a-z]*)/([0-9]{6})/(.*)', 'result',
'/([a-z]*)/latest/(.*)', 'latest_result',
'/([a-z]*)/top', 'latest_top',
'/.*', 'notfound'
)

app = web.application(urls, globals())


PROJECTS = [("en","English"),
            ("de","German"),
            ("fr","French"),
            ("pl","Polish"),
            ("ja","Japanese"),
            ("it","Italian"),
            ("nl","Dutch"),
            ("pt","Portuguese"),
            ("es","Spanish"),
            ("sv","Swedish"),
            ("ru","Russian"),
            ("zh","Chinese"),
            ("zh-classical","Chinese (classical)"),
            ("no","Norwegian"),
            ("fi","Finnish"),
            ("vo","Volapük"),
            ("ca","Catalan"),
            ("ro","Romanian"),
            ("tr","Turkish"),
            ("uk","Ukrainian"),
            ("eo","Esperanto"),
            ("cs","Czech"),
            ("hu","Hungarian"),
            ("sk","Slovak"),
            ("da","Danish"),
            ("id","Indonesian"),
            ("he","Hebrew"),
            ("lt","Lithuanian"),
            ("sr","Serbian"),
            ("sl","Slovenian"),
            ("ar","Arabic"),
            ("ko","Korean"),
            ("bg","Bulgarian"),
            ("et","Estonian"),
            ("new","Newar / Nepal Bhasa"),
            ("hr","Croatian"),
            ("te","Telugu"),
            ("ceb","Cebuano"),
            ("gl","Galician"),
            ("th","Thai"),
            ("el","Greek"),
            ("fa","Persian"),
            ("vi","Vietnamese"),
            ("nn","Norwegian (Nynorsk)"),
            ("ms","Malay"),
            ("simple","Simple English"),
            ("eu","Basque"),
            ("bpy","Bishnupriya Manipuri"),
            ("bs","Bosnian"),
            ("lb","Luxembourgish"),
            ("ka","Georgian"),
            ("is","Icelandic"),
            ("sq","Albanian"),
            ("br","Breton"),
            ("la","Latin"),
            ("az","Azeri"),
            ("bn","Bengali"),
            ("hi","Hindi"),
            ("mr","Marathi"),
            ("tl","Tagalog"),
            ("mk","Macedonian"),
            ("sh","Serbo-Croatian"),
            ("io","Ido"),
            ("cy","Welsh"),
            ("pms","Piedmontese"),
            ("su","Sundanese"),
            ("lv","Latvian"),
            ("ta","Tamil"),
            ("nap","Neapolitan"),
            ("jv","Javanese"),
            ("ht","Haitian"),
            ("Low nds","Saxon"),
            ("scn","Sicilian"),
            ("oc","Occitan"),
            ("ast","Asturian"),
            ("ku","Kurdish"),
            ("hy", "Armenian"),
            ("commons.m","Commons"),
            ("meta.m","Meta")]

class base(object):
    def __init__(self, *args, **kwargs):
        super(base, self).__init__(*args, **kwargs)

class notfound:
    def GET(self):
        return web.notfound()

class about:
    def GET(self):
        render = web.template.render('templates/')
        return render.about()

class latest_top(base):
    def GET(self, proj=None):
        rows = model.get_top(proj)
        render = web.template.render('templates/', base = 'layout', globals = { 'unquote' : urllib.unquote })
        return render.top(rows, config.LATESTTOP)

class index(base):
    def init_form(self, prevform=None):
        years, latest = model.get_dates()
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
        render = web.template.render('templates/', base='layout')
        return render.form(form)
        
    def POST(self): 
        search = web.input()       
        return web.redirect('/%s/%s/%s' % (search['proj'], search['year'], search['inputbox']))
    
    
class result(base): 
    def GET(self,proj=None, year=None, page=None):
        render = web.template.render('templates/', base='layout')
        search = dict(proj=proj, year=year, inputbox=page)
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
        today = datetime.date.today()
        page = search['inputbox']
        date = search['year']
        proj = search['proj']
        page = urllib.unquote(page).strip().replace(" ","_")

        rank = model.get_rank(page, proj)

        if date == 'latest':
            page_counts, execution_time = model.get_latest_stats(page,proj)
        else:
            page_counts, execution_time = model.get_monthly_stats(page,date,proj)
        

        max_count = max(float(max(page_counts)), 1)

        return page_counts, max_count, rank, date, execution_time

# XXX: Hack to support latest 30 days view, rewrite to be prettier.
class latest_result(result):
    def GET(self,proj=None, page=None):
        return result.GET(self, proj, 'latest', page)

    
if __name__ == '__main__':
    if config.DEBUG:
        app.run()
    
