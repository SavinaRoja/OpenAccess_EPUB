# -*- coding: utf-8 -*-

"""
oaepub convert

Convert explicitly listed articles to EPUB, takes input of XML file, DOI, or URL

Usage:
  convert [options] INPUT ...

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -s --silent      print nothing to the console during execution
  -V --verbose     print extra information to the console during execution

Convert Specific Options:
    -l --log=LOG   Specify a location to store the conversion production log
  --no-epubcheck   Disable the use of epubcheck to validate EPUBs
  --no-log         Disable logging entirely
  --no-validate    Disable DTD validation of XML files during conversion. This
                   is only advised if you have pre-validated the files (see
                   'oaepub validate -h')

Convert supports input of the following types:
  XML - Input points to the location of a local XML file (ends with: '.xml')
  DOI - A DOI to be resolved for XML download, if publisher is supported
        (starts with 'doi:')
  URL - A URL link to the article for XML download, if publisher is supported
        (starts with 'http:')

Each individual input will receive its own log (replace '.xml' with '.log')
unless '--log' is used to direct all logging information to a specific file
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