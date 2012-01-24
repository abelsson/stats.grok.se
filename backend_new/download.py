

import urllib2
import re
import datetime
import time
import itertools
import zlib


#import app libs
import settings
from database import Pageview, init_db


def fetchdata(db, url, date, backend):
    #return True
    success = False
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip,deflate')
    
    response = urllib2.urlopen(request)
    #make sure the response is compressed
    isGZipped = response.headers.get('content-type', '').find('gzip') >= 0
    if not isGZipped:
        raise Exception("%s is not a valid gz file." % url)
    
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    
    last_row = []
    content_length = int(response.headers.get('content-length', -1))
     
    mongo_delta = 0
    records = 0
    total_records = 0 
    transferred = 0
    
    
    while True:
        data = response.read(settings.READ_BLOCK_SIZE)
        transferred += len(data)
        if not data:
            #this just assumes that everything went smooth, needs probably some more tests
            success = True
            break
        else:
        #make a file like thing of the read bytes
            data = d.decompress(data)
            
            start = time.time()
            data = data.split('\n')
            if last_row != []:
                ws = 0
                ws += last_row.count(' ') + data[0].count(' ')
                if ws == 3:
                    data[0] = ''.join([last_row, data[0]])
                else:
                    data[0] = ' '.join([last_row, data[0]])

            last_row = data[-1]
            last_row = last_row.split()
            if len(last_row) != 4 or (len(last_row) == 4 and not last_row[-1].endswith('\n')):
                last_row = ' '.join(last_row)
                data = data[:-1]
            else:
                last_row = []
            
            data = transform_data(data, date)
            records += len(data)
            
            timestamp = create_timestamp(url)
            for dat in data:
                key = generate_key(dat['proj'],dat['ns'], dat['title'])
                key = key.encode('utf-8')
                hits = dat['hits']
                db.pageview_collection.insert(Pageview.new(key, hits), timestamp=timestamp)
#                
            mongo_delta += time.time()- start
        
        if settings.DEBUG:
            if records > 10000:
                success= True
                break
                total_records += records
                records = 0
                print 'Downloaded %s Kb (%s%%), processing speed: %s (avg. # records/sec), total records: %s' % (transferred / 1024, (transferred / (content_length / 1024.0)), total_records / mongo_delta, total_records) 
    
    print transferred
    return success

def update_rank(backend, all_time=True, last_30_days=True):
    db = init_db(backend, 'pageviews')
    coll = db.get_collection('pageviews')
    
    cursor = coll.find()
    for article in cursor:
        if all_time:
            pageviews = sum(article['date'].values())
            coll.insert({'_id': article['_id'], 'total': pageviews})
        if last_30_days:
            pageviews = sum(article['date'].values()[:30])
            coll.insert({'_id': article['_id'], 'total30': pageviews})
        
    


def utf8ify(value, original):
    try:
        value = value.decode('utf-8')
    except UnicodeDecodeError:
        #this is a hack and needs to be fixed. 
        value = value.decode('ascii', 'ignore')
        print value, original
    return value
 
 
def create_timestamp(url):
    date =  extract_date(url)
    try:
        timestamp = datetime.datetime.strptime(date, '%Y%m%d-%H')
        return time.mktime(timestamp.timetuple())  
    except ValueError:
        print 'URL: %s; date: %s' % (url,date)
        return time.gmtime()

def generate_key(*args):
    args = [str(arg) if isinstance(arg,int)  else arg for arg in args]
    return  ':'.join(args)


def extract_date(url):
    pos= url.rfind('/') +12
    return url[pos:-7]
    

def transform_data(data, date):
    keys = ['proj', 'title', 'ns', 'hits']
    new_data = []
    for d in data:
        d = d.split()
        if len(d) != 4:
            raise Exception("Data incomplete")
        
        row = {}
        zipper = itertools.izip(keys, d)
        for key, value in zipper:
            if key == 'title' or key =='proj':
                value = utf8ify(value, d)
            elif key == 'ns' or key == 'hits':
                value = int(value)
            row[key] = value
            
        new_data.append(row)
    return new_data
        
    
    

def download_pageviews(backend):
    '''
    New URL: http://dumps.wikimedia.org/other/pagecounts-raw/2011/2011-12/
    Complele URL: http://dumps.wikimedia.org/other/pagecounts-raw/2011/2011-12/pagecounts-20111201-000000.gz
                  
    '''
    today = datetime.datetime.today()
    month = '0%s' % today.month if len(str(today.month)) == 1 else today.month
    url = '%s/%s/%s-%s/' % ('http://dumps.wikimedia.org/other/pagecounts-raw', today.year, today.year, month,)
    print url
    text = urllib2.urlopen(url).read()
    urls = re.findall('a href\="pagecounts\-(.*?)\.gz"', text)
    
    files = dict((generate_key(url, '%s%s.gz' % ('pagecounts-', u)), '%s%s%s.gz' % (url, 'pagecounts-', u)) for u in urls)
    fetched =[]

    db_meta = init_db(backend, 'meta', 'wikistats')
    db_pageviews = init_db(backend, 'pageviews', 'wikistats')
    for filename in files:
        res = db_meta.fetch(ks='meta', key=filename)
        if not res:
            fetched.append(files[filename])
    
#    if settings.DEBUG:
#        fetched = fetched[0:1]
    
    for remote_file in fetched:
        print 'Downloading %s' % remote_file
        success = fetchdata(db_pageviews, remote_file, today, backend)
        print success
        if success:
            print 'Yes, i am going to store %s' % remote_file
            db_meta.store(ks='meta', key=remote_file, columns={'downloaded':1})


def prepare_db(backend):
    if backend=='mongo':
        db = init_db(backend, 'wikistats', 'pageviews')
        coll = db.get_collection('pageviews')
        coll.ensure_index('hash')
        coll.ensure_index('total')
        coll.ensure_index('total30')    


def start():
    backend = 'cassandra'
    prepare_db(backend)
    while True:
        start= time.time()
        download_pageviews(backend)
        update_rank(backend)
        end = time.time()
        timeout = (60 * 60) - (end - start)
        if timeout > 0:
            time.sleep(timeout)

if __name__ == '__main__':
    #update_rank()
    start()
