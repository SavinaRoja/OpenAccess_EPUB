# -*- coding: utf-8 -*-

"""
oaepub batch

Convert all XML files in a directory to individual EPUB files

Usage:
  batch [options] DIR ...

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -s --silent      print nothing to the console during execution
  -V --verbose     print extra information to the console during execution

Batch Specific Options:
    -l --log=LOG   Specify a location to store the collection production log
  --no-epubcheck   Disable the use of epubcheck to validate EPUBs
  --no-log         Disable logging entirely
  --no-validate    Disable DTD validation of XML files during conversion. This
                   is only advised if you have pre-validated the files (see
                   'oaepub validate -h')
  -r --recursive   Recursively traverse subdirectories for conversion


This conversion method, in contrast to 'oaepub convert' supports only XML files.
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