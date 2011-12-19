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
#import datetime
#from time import time
import sys
import os


sys.path.extend([os.path.dirname(__file__)]) #, os.path.join(os.path.dirname(__file__), 'templates')])

import config
import web
from web import form
import model

urls = (
'/', 'index',
'/about', 'about',
'/([a-z.-]*)/([0-9]{6})/(.*)', 'result',
'/([a-z.-]*)/latest/(.*)', 'latest_result',
'/([a-z.-]*)/top', 'latest_top',
'/.*', 'notfound'
)

class base(object):
    def __init__(self, *args, **kwargs):
        super(base, self).__init__(*args, **kwargs)
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates/')
        self.render = web.template.render(self.template_dir, base = 'layout',
                                          globals = { 'unquote' : urllib.unquote,
                                                      'sum' : sum,
                                                      'project_link' : project_link})

    def init_form(self, proj = None, date = None, page = None):
        years, latest = model.get_dates()

        if date == None:
            date = latest
            
        return form.Form(
            form.Dropdown('proj', config.PROJECTS, value=proj, description=''),
            form.Dropdown('year', years, value=date, description=''),
            form.Textbox('inputbox', form.notnull,value=page, id='ib1', description=''),
            form.Button('Top'))

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

        if date == 'latest':
            page_counts, execution_time = model.get_latest_stats(page,proj)
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
        return result.GET(self, proj, 'latest', page)



#
# Utility functions
#
    
def project_link(proj):
    ''' Return the dns host name for a given project '''
    if proj.endswith(".s"):
        return proj[:-2] + ".wikisource.org"

    if proj.endswith(".n"):
        return proj[:-2] + ".wikinews.org"

    if proj.endswith(".m"):
        return proj[:-2] + ".wikimedia.org"

    return proj + ".wikipedia.org"


if __name__ == '__main__':
    if config.DEBUG:
        app = web.application(urls, globals())
        app.run()

application = web.application(urls, globals(), autoreload=False).wsgifunc()
    
