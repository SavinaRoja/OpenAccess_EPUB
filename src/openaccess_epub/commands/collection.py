# -*- coding: utf-8 -*-

"""
oaepub collection

Convert and compile a collection of article XML files into a single EPUB

Usage:
  collection [options] COLLECTION_FILE

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -V --verbose     print extra information to the console during execution
  -s --silent      print nothing to the console during execution

Collection Specific Options:
  -l --log=LOG     Specify a location to store the collection production log
  -p --print-only  Report output only to the console
  --record-pass    Record which XML files pass validation. Without this, only
                   failures will be recorded
  -r --recursive   Recursively traverse subdirectories for validation

To prepare a collection
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