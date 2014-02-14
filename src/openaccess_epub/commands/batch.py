# -*- coding: utf-8 -*-

"""
oaepub batch

Convert all XML files in a directory to individual EPUB files

Usage:
  batch [options] DIR ...

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -V --verbose     print extra information to the console during execution

Batch Specific Options:
  -r --recursive   Recursively traverse subdirectories for conversion
  --no-epubcheck   Disable the use of epubcheck to validate EPUBs
  --no-validate    Disable DTD validation of XML files during conversion. This
                   is only advised if you have pre-validated the files (see
                   'oaepub validate -h')

This
"""

from docopt import docopt


def main(argv=None):
    if argv is None:
        args = docopt(__doc__,
                      version='OpenAccess_EPUB Docoptify 0.1',
                      options_first=True)
    else:
        args = docopt(__doc__,
                      argv=argv,
                      version='OpenAccess_EPUB Docoptify 0.1',
                      options_first=True)
    print(args)

if __name__ == '__main__':
    main()