# -*- coding: utf-8 -*-

"""
oaepub clearcache

Clear out portions or all of OpenAccess_EPUB's cache

Usage:
  clearcache [options] COMMAND

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit

Clearcache Specific Options:
  -d --dry-run     Will print out what it would delete, instead of actually
                   deleting anything. Good idea to try this once before you
                   trust the command (because you are cautious and wise)

Recognized commands for oaepub clearcache are:
  all     Delete all cached data: images, logs
  images  Delete only the cached image files
  logs    Delete only the cached log files
  manual  Print out the cache location then exit

Remember that you can disable any or all caching. Caching is very helpful for
development, but may not be necessary for all users. If you want to manually
alter your cache, you can use 'oaepub clearcache manual' to tell you where the
cache is located.
"""

#Standard Library modules
import os
import platform
import shutil
import subprocess
import sys

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__
import openaccess_epub.utils


def empty_it(path, dry_run):
    if dry_run:
        print('Deleting all contents of {0}'.format(path))
        return
    for root, dirs, files in os.walk(path):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    config = openaccess_epub.utils.load_config_module()

    cache_loc = openaccess_epub.utils.cache_location()

    if args['COMMAND'] == 'manual':
        # We'll *try* to launch a file browser, at least print cache location
        plat = platform.platform()
        if plat.startswith('Windows'):
            os.startfile(cache_loc)
        elif plat.startswith('Darwin'):
            subprocess.Popen(['open', cache_loc])
        elif plat.startswith('Linux'):
            try:
                subprocess.Popen(['xdg-open', cache_loc])
            except OSError:
                pass
        sys.exit('The cache is located at {0}'.format(cache_loc))

    elif args['COMMAND'] == 'logs':
        empty_it(os.path.join(cache_loc, 'logs'), dry_run=args['--dry-run'])
        sys.exit()
    elif args['COMMAND'] == 'images':
        empty_it(config.image_cache, dry_run=args['--dry-run'])
        sys.exit()
    elif args['COMMAND'] == 'all':
        empty_it(os.path.join(cache_loc, 'logs'), dry_run=args['--dry-run'])
        empty_it(config.image_cache, dry_run=args['--dry-run'])
        sys.exit()


if __name__ == '__main__':
    main()