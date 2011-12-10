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

def usedb(name):
    conn = mysqlconn("wikistats")
    c = conn.cursor()
    return conn

if __name__ == "__main__":
    conn = usedb("")
    print conn
    
    c = conn.cursor()
    c.execute("SHOW TABLES LIKE 'pagecounts_%'")
    tbls = c.fetchall()
    print tbls
    subqs = ["select count(*) as rows from %s union" % x for x in tbls]
    q = "select sum(rows) from (%s) as tbl;" % " ".join(subqs)[:-6]
    c.execute(q);
    res = c.fetchone()
    print "Number of rows in pagecounts is %s " % res

    
