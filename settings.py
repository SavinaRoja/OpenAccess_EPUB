import os
import os.path

class Settings(object):
    '''A class for holding settings'''
    def __init__(self):
        #This acquires the local directory
        local = os.getcwd()
        
        #Caching implements storing image files locally in a cache so that
        #the same files need not be repetitively downloaded for the same input
        self.caching = True
        #This sets the cache_location
        self.cache_location = os.path.join(local, 'cache')
        
        #Logging is a good idea, best to leave True
        self.logging = True
        #This sets the location for storing log files
        self.log_location = os.path.join(local, 'logs')
        
        #This controls whether an XML file downloaded from the internet will be
        #saved locally
        self.save_xml = True
        #This sets the downloaded xml file location
        self.xml_location = os.path.join(local, 'downloaded_xml_files')
        
        #This sets a default output location
        self.default_output = os.path.join(local, 'output')
        
        #This determines whether the program will erase the pre-zipped output
        #directory once it finishes zipping it to ePub.
        #It is generally good to leave as True. You can always unzip the ePub.
        self.cleanup = True
        
        #This determines the location of the base_epub directory, which is the
        #reference directory copied to instantiate the epub hierarchy
        self.base_epub = os.path.join('resources', 'base_epub')
        
        #This determines the location of the base css file, which is copied to
        #the ePub's css directory
        self.css_location = os.path.join('resources', 'text.css')
        
        #Configure the location of epubcheck-*.jar.
        self.epubcheck = '../epubcheck/epubcheck-3.0b3.jar'