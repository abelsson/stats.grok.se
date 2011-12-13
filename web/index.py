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

import string,cgi,time
import MySQLdb
import gzip
import urllib
import re
import sys
import datetime

from time import time
from os import curdir, sep
from mod_python import apache, util


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

MONTHS, LATESTMONTH = getdates()
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


HEADER_TEXT = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
   <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
   <!-- All of the CSS and layout came from an example at http://meyerweb.com/eric/css/edge/bargraph/demo.html. -->

   <head>
   <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

   <title>Wikipedia article traffic statistics</title>

   <style type="text/css" media="screen">


   html {background: #909AA9;}
   body {background: #FFF; margin: 0 5%; padding: 1em;
   border: 3px solid gray; border-width: 0 3px;
   font-family: Verdana;
   }
   h1 {font: bold 2em/0.85 Arial, sans-serif; text-align: center; letter-spacing: 1px;
   margin: 1em -0.5em; padding: 0 0.5em;
   border-bottom: 2px solid gray;}

   #q-graph {position: relative; width: 640px; height: 300px;
   margin: 1.1em 0 3.5em; padding: 0;
   background: #DDD;
   border: 2px solid gray; list-style: none;
   font: 9px Helvetica, Geneva, sans-serif;}

   #q-graph ul {margin: 0; padding: 0; list-style: none;}
   #q-graph li {
   position: absolute; bottom: 0; width: 160px; z-index: 2;
   margin: 0; padding: 0;
   text-align: center; list-style: none;
   }
   #q-graph li.qtr {
   padding: 0px;
   margin-left: -7px;
   height: 298px; padding-top: 2px;
   border: 1 px dotted green;
   border-right: 1px dotted #C4C4C4; color: #AAA;}
   #q-graph li.bar {
   width: 15px; border: 1px solid; border-bottom: none; color: #000;
   }
   #q-graph li.bar p {margin: 5px 0 0; padding: 0;}
   #q-graph li.sent {left: 13px; background: #DCA;
   border-color: #EDC #BA9 #000 #EDC;}
   #q-graph li.paid {left: 77px; background: #9D9;
   border-color: #CDC #9B9 #000 #BFB;}

   #q-graph #q1 {left: 0;}
   #q-graph #q2 {left: 160px;}
   #q-graph #q3 {left: 320px;}
   #q-graph #q4 {left: 480px; border-right: none;}

   #q-graph #ticks {width: 640px; height: 300px; z-index: 1;}
   #q-graph #ticks .tick {position: relative; border-bottom: 1px solid #BBB; width: 640px;}
   #q-graph #ticks .tick p {position: absolute; left: 100%; top: -0.67em; margin: 0 0 0 0.5em;}


   div.progress-container {
   border: 1px solid #ccc;
   width: 100px;
   margin: 2px 5px 2px 0;
   padding: 1px;
   float: left;
   background: white;
   }

   div.progress-container > div {
   background-color: #ACE97C;
   height: 12px

   }
   </style>

   <script type="text/javascript">
     function sf() { document.getElementById("ib1").focus(); }
   </script>

<script type="text/javascript">
/* <![CDATA[ */
    (function() {
        var s = document.createElement('script'), t = document.getElementsByTagName('script')[0];

        s.type = 'text/javascript';
        s.async = true;
        s.src = 'http://api.flattr.com/js/0.6/load.js?mode=auto';

        t.parentNode.insertBefore(s, t);
    })();
/* ]]> */
</script>
   </head>

   <body onLoad="sf();">
   <h2>Wikipedia article traffic statistics</h2>
  '''

conn = None
def mysqlconn(db=""):
    global conn

    if conn != None:
        return conn

    try:
        conn = MySQLdb.connect(host = "localhost",
                               user = "wikistats_reader",
                               passwd = "",
                               db = db)
        return conn
    except MySQLdb.Error, e:
        print "Mysql error %s: %s" % (e.args[0],e.args[1])
        conn = None
        raise


def getalldays(c,date):
    c.execute("SHOW TABLES like 'pagecounts_%s__';" % date)
    rows = c.fetchall()
    all_days = [x[0] for x in rows]
    return all_days

def getalldays_new(c,date):
    c.execute("SHOW TABLES like 'pagecounts_%s';" % date)
    rows = c.fetchall()
    all_days = [x[0] for x in rows]
    return all_days

def humround(n):
    if n < 1000:
        return "%.0f" % n
    if n < 1000000:
        return "%.1fk" % (n/1000.0)
    if n < 1000000000:
        return "%.1fM" % (n/1000000.0)


def getcounts(c,date,proj,page):

    all_days = getalldays(c,date)
    counts = {}
    for day in all_days:
        c.execute("SELECT sum(hitcount) FROM "+day+" WHERE page=%s AND project=%s;", (page,proj))
        count = c.fetchone()[0]
        if count == None:
            count = 0
        day = int(day.split("_")[1][-2:])
        counts[day] = int(count)

    return counts

def getcounts_new(c,date,proj,page):

    tables = getalldays_new(c,date)
    counts = {}
    for i in range(0,32):
        counts[i]=0


    if len(tables) != 1:
        raise "Not in new format"

    table = tables[0]

    c.execute("SELECT sum(hitcount),sum(d1), sum(d2), sum(d3), sum(d4), sum(d5), sum(d6), sum(d7), sum(d8), sum(d9), sum(d10), sum(d11), sum(d12), sum(d13), sum(d14), sum(d15), sum(d16), sum(d17), sum(d18), sum(d19), sum(d20), sum(d21), sum(d22), sum(d23), sum(d24), sum(d25), sum(d26), sum(d27), sum(d28), sum(d29), sum(d30), sum(d31) FROM "+table+" WHERE page=%s AND project=%s;", (page,proj))
    count = c.fetchone()

    if count == None:
        return counts

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

def show(proj,date,page,json):
    today = datetime.date.today()
    s = ""

    #if proj != "en":
    #    return "Sorry, only enwiki has stats for now (%s)." % proj


    c = mysqlconn().cursor()

    days = range(1,32)
    page = urllib.unquote(page).strip().replace(" ","_")
    start = time()

    if not json:
        s += HEADER_TEXT

    ssum = 0
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
                counts.extend(getcounts_new(c,m,proj,page).values())
            except:
                counts.extend(getcounts(c,m,proj,page).values())
        counts = counts[-30:]

    else:
        try:
            counts = getcounts_new(c,date,proj,page).values()
        except:
            counts = getcounts(c,date,proj,page).values()


    try:
        maxcount = float(max(counts))
    except:
        maxcount = 1

    if maxcount == 0:
        maxcount = 1

    c.execute("SELECT rank FROM top_"+LATESTTOP+" WHERE project=%s AND page=%s",(proj,page))
    try:
        rank = c.fetchone()[0]
    except:
        rank = -1

    if json:
        #counts=counts[1:]
        v = counts
        s = '''
        {
        "title": "%s",
        "month": "%s",
        "total_views": %s,
        "daily_views": [
                 %s
                 ]
        }''' % (page.replace('\\','\\\\').replace('"','\\"'),date,sum(counts),",".join([str(x) for x in v]))
        c.close()
        return s

    display_proj = proj
    cvt = { "commons.m" : "commons.wikimedia.org",
            "en.n" : "en.wikinews.org",
            "sv.s" : "sv.wikisource.org"}

    try:
        display_proj = cvt[proj]
    except:
        display_proj = proj + ".wikipedia.org"
    s += ('<p><a href="http://'+display_proj+'/wiki/'+ urllib.quote_plus(page) + '">'+page+'</a> has been viewed ')
    s += str(sum(counts))
    if date == -1:
        s += " times in the last 30 days. "
    else:
        s += (" times in %s. " % date)
    if rank != -1:
        s += 'This article ranked %s in traffic on %s.' % (rank,display_proj)

    s += ('</p><ul id="q-graph">\n')

    for i in range(0,31):
        s += ('<li class="qtr" style="width: 25px; left: %dpx;">%d</li>\n' % (i*20,days[i]))


    foo = 0
    for count in counts:

        #count = counts.get(i+1,0)

        s += ('<li class="sent bar" style="height: %dpx; left: %dpx;"><p style="margin-left: -3px;">%s</p></li>\n' % ((count/maxcount)*280,foo,humround(count)))
        foo += 20
        ssum += int(count)

    s += '<li id="ticks">\n'
    for i in range(5,0,-1):
        s += ('<div class="tick" style="height: 59px;"><p>%s</p></div>\n' % humround((maxcount/5*i)*1.071))
    s += ('</li>\n')


    end = time()
    s += '''</ul>
    <form  action="/" method="get">
 <p>Enter another wikipedia article title:<br/>'''

    s+='<select name="proj">'
    for m in PROJECTS:
        selected = ''
        if m[1] == proj:
            selected = 'selected="selected"'

        s+='<option value="%s" %s>%s</option>' % (m[1],selected,m[0])

    s += '</select>'

    if date == -1:
        date = "%d%02d" % (today.year, today.month)
    s+='<select name="year">'

    for m in MONTHS:
        selected = ''
        if m == date:
            selected = 'selected="selected"'

        s+='<option value="%s" %s>%s</option>' % (m,selected,m)

    s += '</select>'



    s += '''
 <input type="text" name="inputbox" size="40" id="ib1" value="%s" />
 <input type="submit" name="button" value="Go" />
 </p>
 </form>''' % (page.replace('"','&quot;'))
    s += '''
 <div style="float: right">
 <a class="FlattrButton" style="display:none;" rev="flattr;button:compact;" href="http://stats.grok.se"></a>
 </div>
    '''
    s += '<p style="font-size: 0.7em">This is very much a beta service and may disappear or change at any time. Questions or comments should go to <a href="http://en.wikipedia.org/wiki/User:Henrik">User:Henrik</a></p>'
    s += '<p style="font-size: 0.6em">(took %f sec)</p>\n' % (end-start)
    s += '</body></html>'
    c.close()

    return s

def print_top(req):

    c = mysqlconn().cursor()

    proj = req.uri.split('/')[1]

    proj = re.sub("[^a-z.\-]","",proj)
    req.send_http_header()
    req.write(HEADER_TEXT)

    c.execute("SELECT rank,project,page,hitcount FROM %s WHERE project='%s' ORDER BY RANK LIMIT 1000" % ("top_"+LATESTTOP, proj))

    req.write('<table>')
    req.write("<p>Most viewed articles in %s</p>" % LATESTTOP)

    req.write("<tr><th>Rank</th><th>Article</th><th>Page views</th></tr>\n")

    num = 0
    rows = c.fetchall()
    for i in rows:
        (rank,proj,page,hitcount) = i
        req.write('<tr><td>%d</td><td><a href="http://stats.grok.se/%s/%s/%s">%s</a></td><td>%s</td></tr>\n' % (rank,proj,LATESTTOP,page,urllib.unquote(page).replace("_"," "),hitcount))
    req.write('</table></body></html>')


def handler(req):
    global conn
    if conn == None:
        conn = mysqlconn("wikistats")
    req.content_type = 'text/html'


    if req.connection.remote_ip == "147.46.178.146" or req.connection.remote_ip == "63.196.132.64" or req.connection.remote_ip == "129.110.5.91":
        req.write("Hello you! Your scraping speed is making the site sluggish and causing problems. Would you consider using the raw dumps at http://dammit.lt/wikistats instead, or limit your requests to something reasonable (1-2 per second). If you have any questions, please post a note at my wikipedia user page (http://en.wikipedia.org/wiki/User:Henrik). \n")
        return apache.OK

    if req.uri == "/about":
        req.send_http_header()
        req.write(HEADER_TEXT)

        req.write('''

        <h3>Frequent questions</h3>
        <div style="margin: 25px 0 10px 0;"><b>Q:</b> What does the stats measure?</div>
        <div style="margin-left: 10px"><b>A:</b> Page views.</div>

        <div style="margin: 25px 0 10px 0;"><b>Q:</b> Where does the data come from?</div>
        <div style="margin-left: 10px"><b>A:</b> <a href="http://dammit.lt">Domas Mituzas</a> put together a system to gather access statistics from wikipedia\'s squid cluster and publishes it <a href="http://dammit.lt/wikistats/">here</a>. This site is a mere visualizer of that data.</div>
        <div style="margin: 25px 0 10px 0;"><b>Q:</b> What is the logic for redirects and when a page gets moved do the stats move?</div>
        <div style="margin-left: 10px"><b>A:</b> It counts the title the page was accessed under, so redirects and moves will unfortunately split the statistics across two different statistics pages. </div>

        <div style="margin: 25px 0 10px 0;"><b>Q:</b>Is the data reliable?</div>
        <div style="margin-left: 10px"><b>A:</b> It is easily susceptible to deliberate attacks and manipulations, but for most articles it should give a fair view of the number of views. I wouldn\'t base any important decisions on these stats. </div>
        <div style="margin: 25px 0 10px 0;"><b>Q:</b>I have another question or comment!</div>
        <div style="margin-left: 10px"><b>A:</b>
        They should be directed at <a href="http://en.wikipedia.org/wiki/User:Henrik">User:Henrik</a> on wikipedia.
        </div>
        ''')
        return apache.OK
    if len(req.uri.split('/')) == 3 and req.uri[-4:] == "/top":
        print_top(req)
        return apache.OK

    if req.uri == "/":
        form = util.FieldStorage(req,keep_blank_values=1)
        inputbox = form.get("inputbox",None)
        year = form.get("year","200712")
        proj = form.get("proj","en")
        act = form.get("button","bla")

        if act=="Top":
            req.headers_out['location'] = '/'+proj+'/top'
            req.status = apache.HTTP_MOVED_TEMPORARILY
            req.send_http_header()
            return apache.HTTP_MOVED_TEMPORARILY

        if inputbox != None:
            req.headers_out['location'] = '/'+proj+'/'+year+'/'+urllib.quote(inputbox)
            req.status = apache.HTTP_MOVED_TEMPORARILY
            req.send_http_header()
            return apache.HTTP_MOVED_TEMPORARILY

        req.send_http_header()
        req.write(HEADER_TEXT)
        req.write('''<p>What do Wikipedia\'s readers care about? Is <a
 href="/en/200712/Britney_Spears">Britney Spears</a> more popular than
 <a href="/en/200712/Brittany">Brittany</a>?  Is <a
 href="/en/200712/Asia_Carrera">Asia Carrera</a> more popular than <a
 href="/en/200712/Asia">Asia</a>? How many people looked at the
 article on <a href="/en/200712/Santa_Claus">Santa Claus</a> in
 December? How many looked at the article on <a
 href="/en/200712/Ron_Paul">Ron Paul</a>?</p>

 <p>What can <i>you</i> find?</p>

 <div style="width: 600px; margin: 20px auto; padding: 30px 0px; text-align: center; background-color:#eee;">
 <form  action="/" method="get">
 <p>Enter a wikipedia article title and press Go<br />''')


        s='<select name="proj">'
        for m in PROJECTS:
            selected = ''
            if m == "en":
                selected = 'selected="selected"'

            s+='<option value="%s" %s>%s</option>' % (m[1],selected,m[0])

        s += '</select>'

        s+='<select name="year">'
        for m in MONTHS:
            selected = ''
            if m == LATESTMONTH:
                selected = 'selected="selected"'

            s+='<option value="%s" %s>%s</option>' % (m,selected,m)

        s += '</select>'

        req.write(s)
        req.write('''
 <input type="text" name="inputbox" id="ib1" value="" />
 <input type="submit" name="button" value="Go" />
 <input type="submit" name="button" value="Top" />
 </p>
 </form>
 <p>
 .. or click "Top" for top 1000 most viewed pages for that project.
 </p>
 </div>

 <h5>News:</h5>
 <ul>
 <li>2008-02-29: Non-english statistics added (available from February) </li>
 <li>2008-03-05: Added <a href="/en/top">top list</a> for English wikipedia. Other projects will be added soon.</li>
 <li>2008-03-19: Top 1000 articles in february for all projects.
 </ul>

 ''')
        req.write('<p style="font-size: 0.7em"><a href="/about">About these stats</a>. The raw data is available <a href="http://dumps.wikimedia.org/other/pagecounts-raw/">here</a>. This is very much a beta service and may disappear or change at any time.</p>')
        req.write('</body></html>')

        return apache.OK


    req.send_http_header()

    json = False
    try:
        a = req.uri.split('/')
        if a[1] == "json":
            i = 2
            json = True
        else:
            i = 1
        proj = a[i]
        if a[i+1]=='latest':
            date = -1
        else:
            date = re.sub("[^0-9]","",a[i+1])
        page = urllib.unquote('/'.join(a[i+2:]))
    except:
        req.write("Malformed URL!")
        return apache.OK

    try:
        if page=="":
            print_top(req)
        else:
            req.write(show(proj,date,page,json))
    except MySQLdb.Error, e:
        conn = None
        req.write( "Mysql error %s: %s" % (e.args[0],e.args[1]))
        conn = mysqlconn("wikistats")
        req.write(show(proj,date,page, json))

    return apache.OK
