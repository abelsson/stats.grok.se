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

import os,re,sys
from sets import Set
from shutil import move, copy
import MySQLdb
import urllib
import datetime
import time
import sgmllib

class LinkParser(sgmllib.SGMLParser):
    def parse(self, s):
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        sgmllib.SGMLParser.__init__(self, verbose)
        self.hyperlinks = []

    def start_a(self, attributes):
        for name, value in attributes:
            if name == "href":
                self.hyperlinks.append(value)

    def get_hyperlinks(self):
        "Return the list of hyperlinks."

        return self.hyperlinks

FETCHED_FILE = "fetched.txt"

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


def download_files(base, urls, fetched):     

    missing = filter(lambda(x): not x in fetched, urls)
    for fn in missing:
        name = fn[:-7].replace("-","_")
        filename = urllib.urlretrieve(base + fn,name)
        print base + fn, " -> ", name
    
def fetchdata():
    
    n = datetime.datetime.now()
    month = n.month
    year = n.year
    
    last_month =  month - 1
    last_year = year    
    if last_month < 1:
        last_month = 12
        last_year -= 1

    url = "http://dumps.wikimedia.org/other/pagecounts-raw/%d/%d-%02d/" % (year, year, month)
    last_url = "http://dumps.wikimedia.org/other/pagecounts-raw/%d/%d-%02d/" % (last_year, last_year, last_month)
    print url
    print last_url

    fetched=[x.strip() for x in file(FETCHED_FILE).readlines()]

    all_urls = []
    parser = LinkParser()
    parser.parse(urllib.urlopen(last_url).read())
    urls = [x for x in parser.get_hyperlinks() if re.search("pagecounts-[0-9]",x) != None]
    all_urls.extend(urls)
    download_files(last_url, urls, fetched)
    
    
    parser = LinkParser()
    parser.parse(urllib.urlopen(url).read())
    urls = [x for x in parser.get_hyperlinks() if re.search("pagecounts-[0-9]",x) != None]
    all_urls.extend(urls)
    download_files(url, urls, fetched)

    f = file(FETCHED_FILE,"w")
    f.writelines([x+"\n" for x in all_urls])
    f.close()

            
def aggregate_day(day,files_for_day):

    print "Sort and unpack"
    for i in files_for_day:
        move(i,"tmp/"+i+".gz")
        os.system("zcat tmp/"+i+".gz | LC_ALL=C sort -S 512M > tmp/"+i)
        os.remove("tmp/"+i+".gz")

    print "Aggregate"
    os.system("LC_ALL=C ./aggregate_day tmp/%s > tmp/%s" % (" tmp/".join(files_for_day),day))

    for i in files_for_day:
        os.remove("tmp/"+i)
    
def load_into_db(day):
    conn = mysqlconn("wikistats")
    c = conn.cursor()
    cwd = os.getcwd()+"/tmp/"
    
    c.execute("CREATE TABLE IF NOT EXISTS tmp_"+day+"  (project VARCHAR(20) NOT NULL, page VARCHAR(255) NOT NULL, hitcount INT(4) NOT NULL);")
    c.execute("LOAD DATA INFILE '"+cwd+day+"' INTO TABLE tmp_"+day+";")
    c.execute("CREATE INDEX "+day+" ON tmp_"+day+" (project,page(32));")
    try:
        c.execute("RENAME TABLE tmp_"+day+" TO "+day+";")
    except:
        print "Couldn't create " + day + ", already exists?"
        
def cleanup(day):
    os.system("gzip tmp/"+day)
    
def do_all_downloaded_days():
    expr = re.compile("pagecounts_[0-9]{8}_[0-9]{2}")

    files = os.listdir(".")
    pagecounts = [e for e in files if expr.match(e)]

    all_days = [e[:-3] for e in pagecounts]
    unique_days = Set(all_days)


    for day in unique_days:
        files_for_day = [e for e in pagecounts if e.startswith(day)]
        day_finished = len(files_for_day) == 24

        if day_finished:
            print "Doing day %s" % day
            aggregate_day(day,files_for_day)
            print "Load into db"
            load_into_db(day)
            print "Cleanup"
            cleanup(day)

def doloop():
    while 1:
        print "Phase 1: Download"
        try:
            fetchdata()
        except:
            time.sleep(60*15)
            continue
        print "Phase 2: Process"
        do_all_downloaded_days()
        print "Phase 3: Sleep"
        sys.stdout.flush() 
        time.sleep(2*60*60)
        
if __name__ == "__main__":
    doloop()

        
