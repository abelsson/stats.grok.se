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

import sys, os, re, time, gc
import MySQLdb
import gzip
import urllib
import datetime

FETCHED_FILE = "/home/henrik/wikistats/fetched.txt"

def mysqlconn(db=""):
    try:
        conn = MySQLdb.connect(host = "localhost",
                               user = "root",
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
    
def get_projects(conn,month):
    c = conn.cursor()

    c.execute("select distinct project from pagecounts_%s" % month)
    rows = c.fetchall()
    return [r[0] for r in rows]

def create_db(conn,month):
     c = conn.cursor()
     cmd = "CREATE TABLE if not exists top_%s (project VARCHAR(22) NOT NULL,page VARCHAR(255) NOT NULL, hitcount INT(4) NOT NULL, rank INT(4) NOT NULL, INDEX(rank), INDEX (project,page(32))); "  % month 
     c.execute(cmd);

def get_top(conn,month,project,num=10000):
    c = conn.cursor()
    c.execute("select project,page,hitcount from pagecounts_"+month+" where project=%s order by hitcount desc limit %s" ,(project,num))
    rows = c.fetchall()

    rank = 1
    res = []
    for r in rows:
        res.append(r+(rank,))
        rank += 1
    return res

def put_in_db(conn,month,values):
    c = conn.cursor()
    
    for v in values:
        c.execute("INSERT INTO top_%s (project,page,hitcount,rank) VALUES %s" % (month,"(%s,%s,%s,%s)"),v)
      
if __name__ == "__main__":
    conn = usedb()
    month = "201012"

    for project in get_projects(conn,month):
        print project
        create_db(conn,month)
        tops = get_top(conn,month,project)
        put_in_db(conn,month,tops)
