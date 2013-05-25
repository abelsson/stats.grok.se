
from pymongo import Connection



class db:
    def __init__(self,  db='wikistats'):
        self.connection = Connection('localhost', 27017)
        self.db =self.connection[db]  
    
    def get_collection(self, collection):
        return self.db[collection]
    
    
    