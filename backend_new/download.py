

#import sys libs
import urllib2
import re
import datetime
import time
import itertools
import zlib


#import app libs
import settings
import database


def fecthdata(url, date):
    success = False
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip,deflate')
    
    response = urllib2.urlopen(request)
    #make sure the response is compressed
    isGZipped = response.headers.get('content-type', '').find('gzip') >= 0
    if not isGZipped:
        raise Exception("%s is not a valid gz file." % url)
    
    d = zlib.decompressobj(16+zlib.MAX_WBITS)
    
    last_row =[]
    dr = '%s-%s' % (date.year, date.month)
    content_length = int(response.headers.get('content-length', -1))
     
    mongo_delta = 0
    records = 0
    total_records = 0 
    transferred = 0
    
    db = database.db()
    coll = db.get_collection('pageviews')
    coll.ensure_index('hash')
        
    
    while True:
        data = response.read(settings.READ_BLOCK_SIZE)
        transferred += len(data)
        if not data:
            #this just assumes that everything went smooth, needs probably some more tests
            success= True
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
            if len(last_row) != 4 or (len(last_row)==4 and not last_row[-1].endswith('\n')):
                last_row = ' '.join(last_row)
                data = data[:-1]
            else:
                last_row=[]
            
            data = transform_data(data, date)
            records += len(data)
            
            batch_new, batch_update= split_data(coll,data)
            if batch_new !=[]:
                coll.insert(batch_new)
            for dat in batch_update:
                #print dat
                key = 'date.%s' % dr
                #db.pageviews.update({'hash': dat['hash']},  { "$inc": {key:dat['date'][dr]}}).explain()
                coll.update({'hash': dat['hash']},  { "$inc": {key:dat['date'][dr]}})
                #print 'done'
                #print coll.find({'hash':dat['hash']}).explain()
                
            mongo_delta += time.time()- start
        
        if settings.DEBUG:
            if records > 10000:
                total_records += records
                records = 0
                print 'Downloaded %s Kb (%s%%), processing speed: %s (avg. # records/sec), total records: %s' % (transferred/1024, ((transferred/1024)/content_length)*100, total_records/mongo_delta, total_records) 
        
    return success

def split_data(coll, data):
    batch_new, batch_update=[],[]
    for d in data:
        res = coll.find_one({'hash': d['hash']})
        if res:
            batch_update.append(d)
        else:
            batch_new.append(d)
    
    return batch_new, batch_update
         

def utf8ify(value):
    try:
        value = value.decode('utf-8')
    except UnicodeDecodeError:
        #this is a hack and needs to be fixed. 
        value = value.encode('ascii', 'ignore')
    return value
    

def generate_hash(proj, title, ns):
    return hash('%s%s%s' % (proj, title, ns))

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
            if key == 'title':
                value = utf8ify(value)
            elif key == 'ns' or key == 'hits':
                value = int(value)
                if key == 'hits':
                    row.setdefault('date', {})
                    dr = '%s-%s' % (date.year, date.month)
                    row['date'][dr] = value
            if not key =='hits':
                row[key]= value
        row['hash'] = generate_hash(row['proj'], row['title'], row['ns'])
        new_data.append(row)
    return new_data
        
    
    

def download_pageviews():
    '''
    New URL: http://dumps.wikimedia.org/other/pagecounts-raw/2011/2011-12/
    Complele URL: http://dumps.wikimedia.org/other/pagecounts-raw/2011/2011-12/pagecounts-20111201-000000.gz
                  
    '''
    today = datetime.datetime.today()
    url = '%s/%s/%s-%s/' % ('http://dumps.wikimedia.org/other/pagecounts-raw', today.year, today.year, today.month)
    text = urllib2.urlopen(url).read()
    urls = re.findall('a href\="pagecounts\-(.*?)\.gz"',text)

    db = database.db()
    coll = db.get_collection('meta')
    #value = re.compile('%s%s%s-([0-9]){6}' % (today.year, today.month,today.day))
    cursor = coll.find()
    fetched= []
    total = cursor.count()
    
    for x in xrange(0, total):
        fetched.append(cursor[x])
    
    #fetched=[x.strip() for x in file(FETCHED_FILE).readlines()]

    missing = filter(lambda(x): not hash(x) in fetched, urls)
    
    if settings.DEBUG:
        missing = missing[0:1]
    
    coll = db.get_collection('meta')
    for i in missing:
        name = "pagecounts-%s.gz" % i#.replace("-","_")#[:-4]
        remote_file = '%s%s' % (url, name)
        print 'Downloading %s' % remote_file
        success = fecthdata(remote_file, today)
        if success:
            coll.insert({hash(url): 1})
         

if __name__ == '__main__':
    download_pageviews()