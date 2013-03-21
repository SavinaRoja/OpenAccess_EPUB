import os.path
import sys
import logging


def cache_location():
    '''Cross-platform placement of cached files'''
    if sys.platform == 'win32':  # Windows
        return os.path.join(os.environ['APPDATA'], 'OpenAccess_EPUB')
    else:  # Mac or Linux
        path = os.path.expanduser('~')
        if path == '~':
            path = os.path.expanduser('~user')
            if path == '~user':
                sys.exit('Could not find the correct cache location')
        return os.path.join(path, 'OpenAccess_EPUB')

LOG = logging.getLogger('Settings')

#Local directory
LOCAL_DIR = os.getcwd()

#Toggle caching
CACHING = True

#Where cache should be
CACHE_LOCATION = cache_location()

#Where cached images should be
CACHE_IMAGES = os.path.join(CACHE_LOCATION, 'img_cache')

#Where to look for images relative to the working directory
DEFAULT_IMAGES = LOCAL_DIR

#Toggle the caching of log files
SAVE_LOG = True

#Where cached log files should be
CACHE_LOG = os.path.join(CACHE_LOCATION, 'logs')

#Where to put the default log file
DEFAULT_LOG = LOCAL_DIR

#Toggle caching of output
SAVE_OUTPUT = False

#Where cached output files should be
CACHE_OUTPUT = os.path.join(CACHE_LOCATION, 'output')

#Where to put the output relative to the working directory
DEFAULT_OUTPUT = LOCAL_DIR

#Where to find the base epub structure
BASE_EPUB = os.path.join(CACHE_LOCATION, 'base_epub')

#A location for a default CSS, overrides base CSS if found
DEFAULT_CSS = LOCAL_DIR

#Where to find the cached/base CSS
CACHE_CSS = os.path.join(CACHE_LOCATION, 'css')

#Where to find the system's epubcheck.jar file
EPUBCHECK = '/home/rulelab/pablo/epubcheck/epubcheck-3.0b3.jar'

LOG.debug('Cache Location: {0}'.format(CACHE_LOCATION))
LOG.debug('Local Directory: {0}'.format(LOCAL_DIR))
LOG.debug('Local Output: {0}'.format(DEFAULT_OUTPUT))
LOG.debug('Local CSS: {0}'.format(DEFAULT_CSS))
