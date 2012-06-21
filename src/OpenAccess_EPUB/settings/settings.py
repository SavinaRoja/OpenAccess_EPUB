import os.path
import sys


class Settings(object):
    """
    "A class for holding settings
    """
    def __init__(self):
        #This acquires the local directory
        local = os.getcwd()

        #This acquires the appropriate directory for storing static/global data
        #If the user encounters an error, or wants to customize the location
        #of their cache, they can do it here.
        self.cache_loc = self.cache_location()

        #Caching implements storing image files locally in a cache so that
        #the same files need not be repetitively downloaded for the same input
        self.caching = True
        #This sets the cache_location
        self.cache_img = os.path.join(self.cache_loc, 'img_cache')

        #Logging is a good idea, best to leave True
        self.logging = True
        #This sets the location for storing log files
        self.local_log = os.path.join(local, 'logs')
        self.save_log = True
        self.cache_log = os.path.join(self.cache_loc, 'logs')

        #This controls whether an XML file downloaded from the internet will be
        #cached
        self.save_xml = True
        #This sets the downloaded xml file location
        self.xml_cache = os.path.join(self.cache_loc, 'downloaded_xml_files')

        #This sets a default output location relative to the directory in which
        #the code is run.
        self.save_output = False
        self.local_output = os.path.join(local, 'output')
        #self.local_output = local
        self.cache_output = os.path.join(self.cache_loc, 'output')

        #This determines whether the program will erase the pre-zipped output
        #directory once it finishes zipping it to ePub.
        #It is generally good to leave as True. You can always unzip the ePub.
        self.cleanup = True

        #This determines the location of the base_epub directory, which is the
        #reference directory copied to instantiate the epub hierarchy
        self.base_epub = os.path.join(self.cache_loc, 'base_epub')

        #This determines the location of the base css file, which is copied to
        #the ePub's css directory
        self.local_css = os.path.join(local, 'css')
        self.cache_css = os.path.join(self.cache_loc, 'css')

        #Configure the location of epubcheck-*.jar.
        self.epubcheck = '../epubcheck/epubcheck-3.0b3.jar'

    def cacheLocation(self):
        """
        This handles where the cache should be located on various OSs.
        """
        if os.name == 'posix':
            s = os.path.expanduser('~')
            if s == '~':
                s = os.path.expanduser('~user')
                if s == '~user':
                    sys.exit('Could not find the correct cache location')
            return os.path.join(s, '.OpenAccess_EPUB')
        if os.name == 'nt':
            s = os.environ['APPDATA']
            return os.path.join(s, '.OpenAccess_EPUB')
