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

import sys
import os
import math
import urllib
import web
import json
from web import form

sys.path.extend([os.path.dirname(__file__)])

import config
import model

urls = (
'/', 'index',
'/about', 'about',
'/([a-z.-]*)/([0-9]{6})/(.*)', 'result',
'/([a-z.-]*)/latest/(.*)', 'latest_result',
'/([a-z.-]*)/latest30/(.*)', 'latest_result',
'/([a-z.-]*)/latest60/(.*)', 'latest_result_60',
'/([a-z.-]*)/latest90/(.*)', 'latest_result_90',
'/([a-z.-]*)/top', 'latest_top',
'/json/([a-z.-]*)/([0-9]{6})/(.*)', 'json_result',
'/json/([a-z.-]*)/latest/(.*)', 'json_latest_result',
'/json/([a-z.-]*)/latest30/(.*)', 'json_latest_result',
'/json/([a-z.-]*)/latest60/(.*)', 'json_latest_result_60',
'/json/([a-z.-]*)/latest90/(.*)', 'json_latest_result_90',
'/.*', 'notfound'
)

class base(object):
    def __init__(self, *args, **kwargs):
        super(base, self).__init__(*args, **kwargs)
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates/')
        self.render = web.template.render(self.template_dir, base = 'layout',
                                          globals = { 'unquote' : urllib.unquote,
                                                      'sum' : sum,
                                                      'project_link' : project_link,
                                                      'round_magnitude' : round_magnitude})

    def init_form(self, proj = None, date = None, page = None):
        years, latest = model.get_dates()

        years.reverse()
        
        if date == None:
            date = latest
            
        return form.Form(
            form.Dropdown('proj', config.PROJECTS, value=proj, description=''),
            form.Dropdown('year', years, value=date, description=''),
            form.Textbox('inputbox', form.notnull,value=page, id='ib1', description=''),
            form.Button('Go', type="submit", value="Go"),
            form.Button('Top'))

#
# 404 page
#
class notfound:
    def GET(self):
        return web.notfound()
    
#
# About page
#
class about(base):
    def GET(self):
        return self.render.about()

#
# Top 1000 viewed articles page
#
class latest_top(base):
    def GET(self, proj=None):
        rows = model.get_top(proj)
        return self.render.top(rows, config.LATESTTOP)

#
# Index page
#
class index(base):
    def GET(self):
        form =  self.init_form()
        return self.render.index(form)
        
    def POST(self): 
        search = web.input()       

        # Top button clicked?
        if search.get('Top') != None:
            return web.redirect('/%s/top' % search['proj'])

        # Nope, regular search
        return web.redirect('/%s/%s/%s' % (search['proj'], search['year'], search['inputbox']))
    
#
# Statistics for a single page for a given month
#
class result(base): 
    def GET(self,proj=None, date=None, page=None):

        if self.block_scraper():
            return self.render.blocked()

        form = self.init_form(proj, date, page)

        counts, rank, execution_time = self.fetch_results(proj, date, page)
        return self.render.results(counts, page, proj, date, rank, execution_time, form)

    def block_scraper(self):
        return web.ctx['ip'] in config.blocked_users    
    
    
    def fetch_results(self, proj, date, page):
        page = urllib.unquote(page).strip().replace(" ","_")

        rank = model.get_rank(page, proj)

        if date.startswith('latest'):
            page_counts, execution_time = model.get_latest_stats(page,proj, int(date[-2:]))
        else:
            page_counts, execution_time = model.get_monthly_stats(page,date,proj)

        return page_counts, rank, execution_time

#
# Statistics for a single page for the latest 30 days
#
# XXX: rewrite to be prettier and less hack-y.
#
class latest_result(result):
    def GET(self,proj=None, page=None):
        return result.GET(self, proj, 'latest30', page)

class latest_result_60(result):
    def GET(self,proj=None, page=None):
        return result.GET(self, proj, 'latest60', page)

class latest_result_90(result):
    def GET(self,proj=None, page=None):
        return result.GET(self, proj, 'latest90', page)


#
# json support
#
class json_result(result):
    def GET(self,proj=None, date=None, page=None):

        if self.block_scraper():
            return self.render.blocked()

        counts, rank, execution_time = self.fetch_results(proj, date, page)
        #web.header('Content-Type', 'application/json')
        return json.dumps({ "title" : page,
                            "month" : date,
                            "daily_views" : counts,
                            "rank" : rank })

    
class json_latest_result(json_result):
    def GET(self,proj=None, page=None):
        return json_result.GET(self, proj, 'latest30', page)

class json_latest_result_60(json_result):
    def GET(self,proj=None, page=None):
        return json_result.GET(self, proj, 'latest60', page)

class json_latest_result_90(json_result):
    def GET(self,proj=None, page=None):
        return json_result.GET(self, proj, 'latest90', page)


#
# Utility functions
#
    
def project_link(proj):
    ''' Return the dns host name for a given project '''
    if proj.endswith(".b"):
        return proj[:-2] + ".wikibooks.org"

    if proj.endswith(".d"):
        return proj[:-2] + ".wiktionary.org"

    if proj.endswith(".s"):
        return proj[:-2] + ".wikisource.org"

    if proj.endswith(".n"):
        return proj[:-2] + ".wikinews.org"

    if proj.endswith(".m"):
        return proj[:-2] + ".wikimedia.org"

    if proj.endswith(".v"):
        return proj[:-2] + ".wikiversity.org"

    if proj.endswith(".w"):
        return proj[:-2] + ".mediawiki.org"

    return proj + ".wikipedia.org"


def round_magnitude(n):
    ''' Return a nice and round number, divisible by 6 which is larger than n'''
    x = n/6.0
    n = math.ceil(x/(10**math.floor(math.log10(x))))
    return int(6.0*n*10**math.floor(math.log10(x)))

if __name__ == '__main__':
    if config.DEBUG:
        app = web.application(urls, globals())
        app.run()

application = web.application(urls, globals(), autoreload=False).wsgifunc()
    
