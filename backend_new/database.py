
from pymongo import Connection

from pycassa import NotFoundException
from pycassa.types import  UTF8Type, IntegerType,BytesType, FloatType
from pycassa.pool import ConnectionPool
from pycassa.columnfamily import ColumnFamily
from pycassa.columnfamilymap import ColumnFamilyMap
from pycassa.system_manager import *

from abc import ABCMeta,abstractmethod

class db(object):
    @abstractmethod
    def __init__(self, collection, db):
        return
    
    @abstractmethod
    def setup(self, **kwargs):
        '''**kwargs should be a dictionary where the key is the name of the function to be called and value the function parameter'''
        return
        
    @abstractmethod
    def get_collection(self, collection):
        return
    
    @abstractmethod
    def store(self, *args, **kwargs):
        return
    
    @abstractmethod
    def fetch(self, *args, **kwargs):
        return

class mongo_db:
    __metaclass__ = ABCMeta
    
    def __init__(self, collection, db):
        self.connection = Connection('localhost', 27017)
        self.db =self.connection[db]  
        self.meta = self.db['meta']
        self.pageviews = self.db['pageviews']
        self.backend = 'mongo_db'
        self.setup()
        
    def setup(self, **kwargs):
        for func, param in kwargs:
            func = getattr(self.collection, func)
            func(param)
    
    def get_collection(self, collection):
        return self.db[collection]
    
    def fetch(self, *args, **kwargs):
        coll = args.pop()
        return coll.find(*args, **kwargs)
    
    def store(self, *args, **kwargs):
        self.collection.update(*args, **kwargs)
    


class cassandra_db:
    __metaclass__ = ABCMeta
    
    def __init__(self, collection, db):
        self.backend = 'cassandra'
        self.port = '9160'
        self.host = '127.0.0.1'
        self.column_families=['pageviews','meta', 'rank']
        self.setup(db)
        self.pool = ConnectionPool(db)
        #create column family Users with comparator=UTF8Type and default_validation_class=UTF8Type and key_validation_class=UTF8Type;
        #autopack_names=False,autopack_values=False
        self.pageviews = ColumnFamily(self.pool, self.column_families[0])#, comparator=UTF8Type(),default_validation_class=BytesType(),key_validation_class=UTF8Type())
        self.meta = ColumnFamily(self.pool, self.column_families[1])#, column_validators={'downloaded': IntegerType},comparator=UTF8Type(),default_validation_class=IntegerType,key_validation_class=UTF8Type())
        self.rank = ColumnFamily(self.pool, self.column_families[2], reversed=True) #)#, comparator=FloatType()
        self.pageview_collection = ColumnFamilyMap(Pageview,  self.pool, 'pageviews')

        
    def setup(self,db):
        mgr = SystemManager('%s:%s' %(self.host, self.port))
        mgr.drop_keyspace('wikistats')
        avail_keyspaces = mgr.list_keyspaces()
        if db not in avail_keyspaces:
            mgr.create_keyspace(db, SIMPLE_STRATEGY, {'replication_factor': '1'})
        
        #avail_column_fams = mgr.get_keyspace_column_families(db, True)
        #for column_fam in self.column_families:
        #    if column_fam not in avail_column_fams:
        mgr.create_column_family(db, 'pageviews',  comparator_type=UTF8Type(),default_validation_class=BytesType(),key_validation_class=UTF8Type())
        mgr.create_column_family(db, 'meta', default_validation_class=IntegerType())
        mgr.create_column_family(db, 'rank', comparator_type=FloatType())
        
                #mgr.alter_column_family(db, collection) #, key_cache_size=42, gc_grace_seconds=1000)
        #print mgr.get_keyspace_column_families(db)
        mgr.close()

    
    def get_collection(self, collection):
        coll = getattr(self, collection)
        return coll
    
    def store(self, *args, **kwargs):
        key = kwargs.get('key')
        columns = kwargs.get('columns')
        timestamp = kwargs.get('timestamp', None)
        cf = getattr(self, kwargs.get('ks'))
        cf.insert(key, columns)
    
    def fetch(self,*args, **kwargs):
        key = kwargs.pop('key')
        ks = kwargs.pop('ks')
        ks = getattr(self, ks)
        try:
            return ks.get(key)
        except NotFoundException:
            return None

class Pageview(object):
    #title =UTF8Type()
    #project= UTF8Type()
    hits = IntegerType()
    #ns = IntegerType()
    
    @classmethod
    def new(cls,key, hits):
        u = cls()
        u.hits=hits
        u.key = key
        return u

#class Pageview(PageviewBase):
#    def __init__(self, title, ns, project, hits):
#        self.titl=title
#        self.ns=ns
#        self.project=project
#        self.hits=hits

      
def init_db(backend, collection, dbname):
    if backend=='mongo':
        mongo_db.register(db)
        store = mongo_db(collection, dbname)
    elif backend=='cassandra':
        cassandra_db.register(db)
        store = cassandra_db(collection, dbname)
    
    return store