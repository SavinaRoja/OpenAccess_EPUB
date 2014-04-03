# -*- coding: utf-8 -*-
"""
Common utility functions
"""

#Standard Library modules
import collections
import logging
import os
import platform
import shutil
import subprocess
import sys

#Non-Standard Library modules

#OpenAccess_EPUB modules
from openaccess_epub.utils.inputs import doi_input, url_input

log = logging.getLogger('openaccess_epub.utils')

Identifier = collections.namedtuple('Identifer', 'id, type')


#Python documentation refers to this recipe for an OrderedSet
#http://code.activestate.com/recipes/576694/
class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


def cache_location():
    '''Cross-platform placement of cached files'''
    plat = platform.platform()
    log.debug('Platform read as: {0}'.format(plat))
    if plat.startswith('Windows'):
        log.debug('Windows platform detected')
        return os.path.join(os.environ['APPDATA'], 'OpenAccess_EPUB')
    elif plat.startswith('Darwin'):
        log.debug('Mac platform detected')
    elif plat.startswith('Linux'):
        log.debug('Linux platform detected')
    else:
        log.warning('Unhandled platform for cache_location')

    #This code is written for Linux and Mac, don't expect success for others
    path = os.path.expanduser('~')
    if path == '~':
        path = os.path.expanduser('~user')
        if path == '~user':
            log.critical('Could not resolve the correct cache location')
            sys.exit('Could not resolve the correct cache location')
    cache_loc = os.path.join(path, '.OpenAccess_EPUB')
    log.debug('Cache located: {0}'.format(cache_loc))
    return cache_loc


def config_location():
    """
    Returns the expected location of the config file
    """
    return os.path.join(cache_location(), 'config.py')


def base_epub_location():
    """
    Returns the expected location of the base_epub directory
    """
    return os.path.join(cache_location(), 'base_epub')


def publisher_plugin_location():
    """
    Returns the expected location of the publisher_plugins directory.
    """
    return os.path.join(cache_location(), 'publisher_plugins')


def load_config_module():
    """
    If the config.py file exists, import it as a module. If it does not exist,
    call sys.exit() with a request to run oaepub configure.
    """
    import imp
    config_path = config_location()
    try:
        config = imp.load_source('config', config_path)
    except IOError:
        log.critical('Config file not found. oaepub exiting...')
        sys.exit('Config file not found. Please run \'oaepub configure\'')
    else:
        log.debug('Config file loaded from {0}'.format(config_path))
        return config


def mkdir_p(dir):
    if os.path.isdir(dir):
        return
    os.makedirs(dir)


def evaluate_relative_path(working=os.getcwd(), relative=''):
    """
    This function receives two strings representing system paths. The first is
    the working directory and it should be an absolute path. The second is the
    relative path and it should not be absolute. This function will render an
    OS-appropriate absolute path, which is the normalized path from working
    to relative.
    """
    return os.path.normpath(os.path.join(working, relative))


def get_absolute_path(some_path):
    """
    This function will return an appropriate absolute path for the path it is
    given. If the input is absolute, it will return unmodified; if the input is
    relative, it will be rendered as relative to the current working directory.
    """
    if os.path.isabs(some_path):
        return some_path
    else:
        return evaluate_relative_path(os.getcwd(), some_path)


def get_output_directory(args):
    """
    Determination of the directory for output placement involves possibilities
    for explicit user instruction (absolute path or relative to execution) and
    implicit default configuration (absolute path or relative to input) from
    the system global configuration file. This function is responsible for
    reliably returning the appropriate output directory which will contain any
    log(s), ePub(s), and unzipped output of OpenAccess_EPUB.

    It utilizes the parsed args, passed as an object, and is self-sufficient in
    accessing the config file.

    All paths returned by this function are absolute.
    """
    #Import the global config file as a module
    import imp
    config_path = os.path.join(cache_location(), 'config.py')
    try:
        config = imp.load_source('config', config_path)
    except IOError:
        print('Could not find {0}, please run oae-quickstart'.format(config_path))
        sys.exit()
    #args.output is the explicit user instruction, None if unspecified
    if args.output:
        #args.output may be an absolute path
        if os.path.isabs(args.output):
            return args.output  # return as is
        #or args.output may be a relative path, relative to cwd
        else:
            return evaluate_relative_path(relative=args.output)
    #config.default_output for default behavior without explicit instruction
    else:
        #config.default_output may be an absolute_path
        if os.path.isabs(config.default_output):
            return config.default_output
        #or config.default_output may be a relative path, relative to input
        else:
            if args.input:  # The case of single input
                if 'http://www' in args.input:
                    #Fetched from internet by URL
                    raw_name = url_input(args.input, download=False)
                    abs_input_path = os.path.join(os.getcwd(), raw_name+'.xml')
                elif args.input[:4] == 'doi:':
                    #Fetched from internet by DOI
                    raw_name = doi_input(args.input, download=False)
                    abs_input_path = os.path.join(os.getcwd(), raw_name+'.xml')
                else:
                    #Local option, could be anywhere
                    abs_input_path = get_absolute_path(args.input)
                abs_input_parent = os.path.split(abs_input_path)[0]
                return evaluate_relative_path(abs_input_parent, config.default_output)
            elif args.batch:  # The case of Batch Mode
                #Batch should only work on a supplied directory
                abs_batch_path = get_absolute_path(args.batch)
                return abs_batch_path
            elif args.zip:
                #Zip is a local-only option, behaves just like local xml
                abs_input_path = get_absolute_path(args.zip)
                abs_input_parent = os.path.split(abs_input_path)[0]
                return evaluate_relative_path(abs_input_parent, config.default_output)
            elif args.collection:
                return os.getcwd()
            else:  # Un-handled or currently unsupported options
                print('The output location could not be determined...')
                sys.exit()


def file_root_name(name):
    """
    Returns the root name of a file from a full file path.

    It will not raise an error if the result is empty, but an warning will be
    issued.
    """
    base = os.path.basename(name)
    root = os.path.splitext(base)[0]
    if not root:
        warning = 'file_root_name returned an empty root name from \"{0}\"'
        log.warning(warning.format(name))
    return root


def files_with_ext(extension, directory='.', recursive=False):
    """
    Generator function that will iterate over all files in the specified
    directory and return a path to the files which possess a matching extension.

    You should include the period in your extension, and matching is not case
    sensitive: '.xml' will also match '.XML' and vice versa.

    An empty string passed to extension will match extensionless files.
    """
    if recursive:
        log.info('Recursively searching {0} for files with extension "{1}"'.format(directory, extension))
        for dirname, subdirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirname, filename)
                _root, ext = os.path.splitext(filepath)
                if extension.lower() == ext.lower():
                    yield filepath

    else:
        log.info('Looking in {0} for files with extension:  "{1}"'.format(directory, extension))
        for name in os.listdir(directory):
            filepath = os.path.join(directory, name)
            if not os.path.isfile(filepath):  # Skip non-files
                continue
            _root, ext = os.path.splitext(filepath)
            if extension.lower() == ext.lower():
                yield filepath


def epubcheck(epubname, config=None):
    """
    This method takes the name of an epub file as an argument. This name is
    the input for the java execution of a locally installed epubcheck-.jar. The
    location of this .jar file is configured in config.py.
    """
    if config is None:
        config = load_config_module()
    r, e = os.path.splitext(epubname)
    if not e:
        log.warning('Missing file extension, appending ".epub"')
        e = '.epub'
        epubname = r + e
    elif not e == '.epub':
        log.warning('File does not have ".epub" extension, appending it')
        epubname += '.epub'
    subprocess.call(['java', '-jar', config.epubcheck_jarfile, epubname])


def dir_exists(directory):
    """
    If a directory already exists that will be overwritten by some action, this
    will ask the user whether or not to continue with the deletion.

    If the user responds affirmatively, then the directory will be removed. If
    the user responds negatively, then the process will abort.
    """
    log.info('Directory exists! Asking the user')
    reply = input('''The directory {0} already exists.
It will be overwritten if the operation continues.
Replace? [Y/n]'''.format(directory))
    if reply.lower() in ['y', 'yes', '']:
        shutil.rmtree(directory)
        os.makedirs(directory)
    else:
        log.critical('Aborting process, user declined overwriting {0}'.format(directory))
        sys.exit('Aborting process!')


suggested_article_types = ['abstract', 'addendum', 'announcement',
    'article-commentary', 'book-review', 'books-received', 'brief-report',
    'calendar', 'case-report', 'collection', 'correction', 'discussion',
    'dissertation', 'editorial', 'in-brief', 'introduction', 'letter',
    'meeting-report', 'news', 'obituary', 'oration', 'partial-retraction',
    'product-review', 'rapid-communication', 'rapid-communication', 'reply',
    'reprint', 'research-article', 'retraction', 'review-article',
    'translation']
