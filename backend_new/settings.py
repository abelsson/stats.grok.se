import os
import sys

if sys.platform.startswith('win'):
    ROOT = 'c:\\'
else:
    ROOT = '/'

DEBUG = True

HOST= 'localhost'
USER ='wikistats'
PASSWD ='wikistats'
DB = 'wikistats'

READ_BLOCK_SIZE = 1024*8
FETCHED_DIR = os.path.join(ROOT, 'storage', 'wikistats')