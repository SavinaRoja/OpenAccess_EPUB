import os
import os.path

class Settings(object):
    '''A class for holding settings'''
    def __init__(self):
        #Set the cache location
        local = os.getcwd()
        path = 'cache'
        self.cache_location = os.path.join(local, path)