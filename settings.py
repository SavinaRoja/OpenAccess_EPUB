import os
import os.path

class Settings(object):
    '''A class for holding settings'''
    def __init__(self):
        #Set the cache location
        local = os.getcwd()
        
        self.caching = True
        self.cache_location = os.path.join(local, 'cache')
        self.logging = True
        self.save_xml = True
        self.default_output = os.path.join(local, 'output')
        self.cleanup = True