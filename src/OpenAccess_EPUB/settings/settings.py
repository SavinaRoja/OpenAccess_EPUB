import os.path
import sys
import logging

log = logging.getLogger('Settings')


class Settings(object):
    """
    "A class for holding settings
    """
    def __init__(self):
        #This acquires the local directory
        self.local = os.getcwd()

        #This acquires the appropriate directory for storing static/global data
        #If the user encounters an error, or wants to customize the location
        #of their cache, they can do it here.
        self.cache_loc = self.cacheLocation()

        #Caching implements storing image files locally in a cache so that
        #the same files need not be repetitively downloaded for the same input
        self.caching = True
        #This sets the cache_location
        self.cache_img = os.path.join(self.cache_loc, 'img_cache')

        #This sets the default relative location for finding image files
        #self.default_images = os.path.join(self.local, 'images')
        self.default_images = self.local

        #This sets the location for storing log files
        self.save_log = True
        self.cache_log = os.path.join(self.cache_loc, 'logs')

        #This sets a default output location relative to the directory in which
        #the code is run.
        self.save_output = False
        self.local_output = os.path.join(self.local)

        #This determines whether the program will erase the pre-zipped output
        #directory once it finishes zipping it to ePub.
        #It is generally good to leave as True. You can always unzip the ePub.
        self.cleanup = True

        #This determines the location of the base_epub directory, which is the
        #reference directory copied to instantiate the epub hierarchy
        self.base_epub = os.path.join(self.cache_loc, 'base_epub')

        #This determines the location of the base css file, which is copied to
        #the ePub's css directory
        self.local_css = os.path.join(self.local, 'css')
        self.cache_css = os.path.join(self.cache_loc, 'css')

        #Configure the location of epubcheck-*.jar.
        self.epubcheck = '/home/pablo/epubcheck/epubcheck-3.0b3.jar'

        #Record settings in log
        self.logSettings()

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
            return os.path.join(s, 'OpenAccess_EPUB')

    def logSettings(self):
        """
        Make log statements for settings which might be useful for debugging.
        """
        log.debug('Cache Location: {0}'.format(self.cache_loc))
        log.debug('Local: {0}'.format(self.local))
        log.debug('Local Output: {0}'.format(self.local_output))
        log.debug('Local CSS: {0}'.format(self.local_css))
        log.debug('Cleanup: {0}'.format(self.cleanup))
