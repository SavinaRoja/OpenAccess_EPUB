# -*- coding: utf-8 -*-

"""
oaepub epubzip

Zip an unzipped EPUB file (as directory) back into a valid EPUB (mimetype first)

Usage:
  epubzip [options] EPUBDIR

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
"""

#Standard Library modules

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__
from openaccess_epub.utils.epub import epub_zip


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    epub_zip(args['EPUBDIR'])


if __name__ == '__main__':
    main()