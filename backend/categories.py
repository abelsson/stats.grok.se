#!/usr/bin/env python

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
sys.path.append('/usr/lib/python%s/site-packages/oldxml' % sys.version[:3])

import urllib
import re
from xml.dom.ext.reader import Sax2
import MySQLdb
import gzip
import datetime

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

URL = "http://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:%s&cmsort=timestamp&cmdir=desc&cmlimit=500&format=xml" % (sys.argv[1])

text = urllib.urlopen(URL)
reader = Sax2.Reader()
# parse the document
doc = reader.fromStream(text)

members = doc.getElementsByTagName("cm")

subcategories = []
titles = []
for m in members:
    ns = m.attributes[(None,'ns')].value
    title = m.attributes[(None,'title')].value

    if ns == '14':
        subcategories.append(title)
    else:
        titles.append(title)


print "======= Categories ========"
for i in subcategories:
    print i.encode("utf-8")
    
conn = mysqlconn("wikistats")
c = conn.cursor()

hittitles = []
query = "SELECT hitcount,page FROM pagecounts_200902 WHERE project='en' AND page IN ("
print "======= Titles ========"
for i in titles:
    title = i.encode("utf-8").replace(" ","_").replace('"', '\\"').replace("'", "\\'");
    query = query + "'%s'," % title
  

query= query[:-1]+");"
print query
c.execute(query)
rows = c.fetchall()

x = {}
for r in rows:
    print r
    hits = int(r[0])
    title = r[1]
    x[title.lower()]=x.get(title.lower(),0)+hits

print x

hittitles.sort(reverse=True)

for i in x.keys():
    (hit, title) = (x[i],i)
    print title.capitalize(), hit
    
