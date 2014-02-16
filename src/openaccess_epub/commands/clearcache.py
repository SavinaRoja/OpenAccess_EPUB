# -*- coding: utf-8 -*-

"""
oaepub clearcache

Clear out portions or all of OpenAccess_EPUB's cache

Usage:
  clearcache [options] COMMAND

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -V --verbose     print extra information to the console during execution

Clearcache Specific Options:
  -d --dry-run     Will print out what it would delete (like --verbose), but not
                   delete anything. Good idea to try this once before you trust
                   the command (because you are cautious and wise)

Recognized commands for oaepub clearcache are:
  all     Delete all cached data: images, logs, and XML
  images  Delete only the cached image files
  logs    Delete only the cached log files
  manual  Print out the cache location then exit
  xml     Delete only the cached XML files

Remember that you can disable any or all caching. Caching is very helpful for
development, and may not be necessary for all users. If you want to manually
alter your cache, you can use 'oaepub clearcache manual' to tell you where the
cache is located.
"""

from docopt import docopt


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB Docoptify 0.1',
                  options_first=True)
    print(args)

if __name__ == '__main__':
    main()