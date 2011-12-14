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

FETCHED_FILE = "/storage/wikistats/fetched.txt"

def mysqlconn(db=""):
    return
    try:
        conn = MySQLdb.connect(host = "localhost",
                               user = "wikistats",
                               passwd = "",
                               db = db)
        return conn
    except MySQLdb.Error, e:
        print "Mysql error %d: %d" % (e.args[0],e.args[1])
        sys.exit(1)
        
def createdb():
    conn = mysqlconn()
    c = conn.cursor()
    cmd = "create database wikistats;"
    try:
        c.execute(cmd)
    except MySQLdb.Error, e:
        if e.args[0] == 1007:
            pass
        else:
            raise
    conn.close();

def usedb(name):
    conn = mysqlconn("wikistats")
    c = conn.cursor()

    return conn

def insert_list(c,name,lines):

    print name

    return

    try:
        c.execute("SELECT * FROM %s LIMIT 1;" % name)
        print "Table %s alredy exists, skipping" % name
        return
    except:
        cmd = "CREATE TABLE if not exists %s (project VARCHAR(20), page VARCHAR(255), hitcount INT(4), d1 INT(4),  d2 INT(4),  d3 INT(4),  d4 INT(4),  d5 INT(4),  d6 INT(4),  d7 INT(4),  d8 INT(4),  d9 INT(4),  d10 INT(4),  d11 INT(4),  d12 INT(4),  d13 INT(4),  d14 INT(4),  d15 INT(4),  d16 INT(4),  d17 INT(4),  d18 INT(4),  d19 INT(4),  d20 INT(4),  d21 INT(4),  d22 INT(4),  d23 INT(4),  d24 INT(4),  d25 INT(4),  d26 INT(4),  d27 INT(4),  d28 INT(4),  d29 INT(4),  d30 INT(4),  d31 INT(4), INDEX (page)); "  % name # , PRIMARY KEY(pps));"
        c.execute(cmd);
        pass
    

    i = 0
    start = time.time()
    tmp = []
    c.execute("LOCK TABLE %s WRITE;" % name);
    c.execute("ALTER TABLE %s DISABLE KEYS" % name)

    isdict = False
    if type(lines) == type({}):
        isdict = True
        
        #for line in lines:
    while 1:
        line = lines.readline()
        if line == '':
            break
        
        try:
            if isdict:
                proj = "en"
                page = line
                nums = lines[line]
            else:
                ar = line.split()
                proj = ar[0]
                page = ar[1].replace(" ","_")
                nums = ar[2][:-1].split(",")
        
            tmp.append(proj)
            tmp.append(urllib.unquote(page)[:255])
            [a.append(x) for x in nums]
            
            if i % 10000 == 9999:
                fmt = "(%s,%s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)," * (len(tmp)/3)
                fmt = fmt[:-1]


                
                c.execute("INSERT INTO %s (project,page,hitcount,d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20, d21, d22, d23, d24, d25, d26, d27, d28, d29, d30, d31) VALUES %s;" % (name,fmt), tuple(tmp))
          
                tmp = []
                c.execute("UNLOCK TABLES;");
                c.execute("LOCK TABLE %s WRITE;" % name);
                now = time.time()
                avg = i / (now - start)
                sys.stdout.write("\033[GAdding proj %s (%d total, avg %d texts/sec)                " % (proj,i+1, avg))
                sys.stdout.flush()
            
            i = i + 1
        except:
            c.execute("UNLOCK TABLES;");
            raise

    if tmp != []:
        fmt = "(%s,%s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)," * (len(tmp)/3)
        fmt = fmt[:-1]
        c.execute("INSERT INTO %s (project,page,hitcount,d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20, d21, d22, d23, d24, d25, d26, d27, d28, d29, d30, d31) VALUES %s;" % (name,fmt), tuple(tmp))

    if isdict:
        lines = {}
        gc.collect()
        
    c.execute("UNLOCK TABLES;");
    c.execute("ALTER TABLE %s ENABLE KEYS" % name)
        
    
def readfile(conn, name, filename):
    print name
    
    c = conn.cursor()
    insert_list(c,name,gzip.GzipFile(filename,"rb"))    


def readfile_dict(conn, filename):
    foo = {}
    
    for line in file(filename,"r").readlines():    
        try:
            ar = line.split()
            proj = ar[0]
            page = ar[1]
            num = int(ar[2])

            pps = md5.md5(proj + page).hexdigest()
        
            if not foo.has_key(pps):
                foo[pps] = num
            else:
                foo[pps] = foo[pps] + num

        except:
            raise

def aggregate_day_old(conn,day):
    for r in rows:
        print r[0]
        l = 100000
        o = 0
        c = conn.cursor()
        
        c.execute("SELECT page,hitcount FROM %s LIMIT %d OFFSET %d ORDER BY page" % (r[0],l,o))
        rows = c.fetchall()
        length = len(rows)
        start = time.time()
        while length > 0:
            o += length
            for p in rows:
                pg = p[0]
                num = int(p[1])
                stats[pg] = stats.get(pg, 0) + num
                    
            c.execute("SELECT page,hitcount FROM %s LIMIT %d OFFSET %d ORDER BY page" % (r[0],l,o))
            rows = c.fetchall()
            length = len(rows)

        end = time.time()
        print "Time:", (end - start), " elements = ", len(stats)
        c.close()
        gc.collect()
        
    c = conn.cursor()
    
    insert_list(c,"pagecounts_%s" % day,stats)



idxs = {}
cache = {} # start, length, rows 
 

def peek(c,pos):
    
    if idxs[pos] >= cache[pos][0] + cache[pos][1]:
        c.execute("SELECT page,hitcount FROM %s ORDER BY 'page' LIMIT %d OFFSET %d  " % (pos,50000,idxs[pos]))
        rows = c.fetchall()
        cache[pos][0] += cache[pos][1]
        cache[pos][1] = len(rows)
        cache[pos][2] = rows
        
        if len(rows) == 0:
            idxs[pos] = -1

    try:
        return cache[pos][2][idxs[pos]-cache[pos][0]]
    except IndexError:
        return ('',0)


def get(c,pos):
    e = peek(c,pos)
    idxs[pos] += 1
    if peek(c,pos) == None:
        idxs[pos] = -1

    return e


def aggregate_day(conn,day):
    tablename = "pagecounts_%s" % day

    c = conn.cursor()
    c.execute("SHOW TABLES like 'pagecounts_%s_%%';" % day)

    rows = [x[0] for x in c.fetchall()]
    all = []
    print rows
    if len(rows) != 24:
        print "Day not fully fetched"
        return
    
    for r in rows:
        idxs[r] = 0
        cache[r] = [0,0,[]]
        c.execute("ALTER TABLE %s  CONVERT TO CHARACTER SET binary" % r)
    tmp = []
    num = 0

    
    try:
        c.execute("SELECT * FROM %s LIMIT 1;" % tablename)
        print "Table %s alredy exists, skipping" % tablename
        return
    except:
        cmd = "CREATE TABLE if not exists %s (project VARCHAR(20), page VARCHAR(255), hitcount INT(4), INDEX (page)); "  % tablename # , PRIMARY KEY(pps));"
        c.execute(cmd);
        
    

    i = 0
    start = time.time()
    tmp = []
    c.execute("ALTER TABLE %s DISABLE KEYS" % tablename)
    
    while 1:
        if max(idxs.values()) == -1:
            break
    

        mins = [(peek(c,i)[0],i) for i in rows if idxs[i] >= 0]

        name = min(mins)[0]
        cnt = 0

        for i in mins:
            assert i[0] >= name
            if i[0] == name:
                cnt += get(c,i[1])[1]


        tmp.append("en")
        tmp.append(urllib.unquote(name)[:255])
        tmp.append(int(cnt))

        
        num += 1
        if num % 1000 == 999:

            fmt = "(%s,%s,%s)," * (len(tmp)/3)
            fmt = fmt[:-1]


            c.execute("INSERT INTO %s (project,page,hitcount) VALUES %s;" % (tablename,fmt), tuple(tmp))
            tmp = []

            now = time.time()
            avg = num / (now - start)
            
            sys.stdout.write("\033[GAdding %s (%d total, avg %d texts/sec)                " % (name.replace('\n','')[:25].ljust(25),num, avg))
            sys.stdout.flush()

    if tmp != []:
        fmt = "(%s,%s,%s)," * (len(tmp)/3)
        fmt = fmt[:-1]
        c.execute("INSERT INTO %s (project,page,hitcount) VALUES %s;" % (tablename,fmt), tuple(tmp))

            
    c.execute("ALTER TABLE %s ENABLE KEYS" % tablename)

    c.close()
    
def aggregate_all(conn):
    c = conn.cursor()
    c.execute("SHOW TABLES like 'pagecounts_________';")
    c.close()
    rows = c.fetchall()
    all = []
    stats = {}
    print rows

    for r in rows:
        print r[0]
        l = 100000
        o = 0
        c = conn.cursor()
        
        c.execute("SELECT page,hitcount FROM %s LIMIT %d OFFSET %d" % (r[0],l,o))
        rows = c.fetchall()
        length = len(rows)
        start = time.time()
        while length > 0:
            o += length
            for p in rows:
                pg = p[0]
                num = int(p[1])
                stats[pg] = stats.get(pg, 0) + num
                    
            c.execute("SELECT page,hitcount FROM %s LIMIT %d OFFSET %d" % (r[0],l,o))
            rows = c.fetchall()
            length = len(rows)

        end = time.time()
        print "Time:", (end - start), " elements = ", len(stats)
        c.close()
        gc.collect()
        
    c = conn.cursor()
    
    insert_list(c,"december",stats)

def aggregate_all_alias(conn):
    c = conn.cursor()
    c.execute("SHOW TABLES like 'pagecounts_________';")
    rows = c.fetchall()
    all = []
    for r in rows:
        print r[0]
        c.execute("ALTER TABLE %s ENABLE KEYS" % r[0])
        all.append(r[0])

    tables = ",".join(all);
    try:
        c.execute("DROP TABLE total");
    except:
        pass
    
    cmd = "CREATE TABLE if not exists total (project VARCHAR(20), page VARCHAR(255), hitcount INT(4), INDEX (page)) ENGINE = MERGE UNION=(%s); "  % (tables)
    c.execute(cmd)

def fetchdata():
    text = urllib.urlopen("http://dammit.lt/wikistats/").read()
    urls = re.findall('a href\="pagecounts\-(.*?)\.gz"',text)

    fetched=[x.strip() for x in file(FETCHED_FILE).readlines()]

    missing = filter(lambda(x): not x in fetched, urls)
    for i in missing:
        name = ("pagecounts-%s" % i).replace("-","_")[:-4]
        filename = urllib.urlretrieve("http://dammit.lt/wikistats/pagecounts-%s.gz" % i,name)
        print "http://dammit.lt/wikistats/pagecounts-%s.gz" % i 

        #readfile(conn, name, filename[0])
        print

    f = file(FETCHED_FILE,"w")
    f.writelines([x+"\n" for x in urls])
    f.close()
    
if __name__ == "__main__":
    fn = sys.argv[1]
    name = fn.split("/")[-1].split(".")[0].replace("-","_")
    #conn = usedb(name)    
    if fn == "--aggregate":
        aggregate_all_alias(conn);
    elif fn == "--fetch":
        fetchdata()
    elif fn == "--aggregate-day":
        try:
            day = sys.argv[2]
        except:
            day = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        aggregate_day(conn,day)
    elif fn == "--yesterday":
        day = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        print day
        conn.close()
        sys.exit(0)
    else:
        readfile(conn,name,fn)


    print
    
