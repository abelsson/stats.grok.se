#! /usr/bin/env python

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

import sys, os, re, md5, time, gc
import MySQLdb
import gzip
import urllib
import datetime

LATESTMONTH = "200912"

def mysqlconn(db=""):
    try:
        conn = MySQLdb.connect(host = "localhost",
                               user = "wikistats",
                               passwd = "",
                               db = db)
        return conn
    except MySQLdb.Error, e:
        print "Mysql error %d: %d" % (e.args[0],e.args[1])
        sys.exit(1)
        


def usedb():
    conn = mysqlconn("wikistats")
    c = conn.cursor()

    return conn
    

def do():
    c = conn.cursor()
    
    
    titles = [x.strip() for x in file("template-blp-unsourced.txt").readlines()]


    #print titles
    print "Making query"
    
    hittitles = []
    query = ""
    query = "SELECT hitcount,page FROM pagecounts_"+LATESTMONTH+" WHERE project='en' AND page IN ("

    if len(titles) == 0:
        print ( "<li>none</li></ol>")
        return


    talk_titles = [ x[5:] for x in titles if x[0:5] == "Talk:"]
    titles = talk_titles + [ x for x in titles if x[0:5] != "Talk:"]

    for title in titles:
        title = title.replace("'","\\'")    
        query = query + "'%s'," % title

    
    #print query
    query= query[:-1]+");"
    #req.write(query)

    print "Execute query"
    c.execute(query)
    rows = c.fetchall()

    print "Got %d rows" % len(rows)

    print "Fix"
    km = {}
    for r in rows:
        #print r
        hits = int(r[0])
        title = r[1]
        km[title.lower()]=km.get(title.lower(),0)+hits

    #print km
    print "Sort"
    foo = [ (km[x],x) for x in km.keys()]
    foo.sort(reverse=True)

    print( "<html><head></head><body><h3>Unreferenced BLPs in order of popularity</h3>\n<ol>\n")
    for i in foo:
        (hit, t) = i
        try:
            t = t.replace(" ","_").replace('"', '\\"').replace("'", "\\'")
            t = [x for x in titles if x.lower() == t.lower()][0].replace('\\"', '"').replace("\\'", "'")
        except:
            t = t + " (aiee) "
        print('<li><a href="http://en.wikipedia.org/wiki/%s">%s</a> %d </li>\n' % (t,t.replace("_"," "),hit))
    
    print("</ol></body></html>")

if __name__ == "__main__":
    conn = usedb()
    month = "200808"
    do()
