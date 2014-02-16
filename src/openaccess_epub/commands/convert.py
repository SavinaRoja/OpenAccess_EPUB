# -*- coding: utf-8 -*-

"""
oaepub convert

Convert explicitly listed articles to EPUB, takes input of XML file, DOI, or URL

Usage:
  convert [--silent | --echo-log] [options] INPUT ...

General Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -s --silent      print nothing to the console during execution
  -V --verbose     print extra information to the console during execution

Convert Specific Options:
  --no-cleanup     The EPUB contents prior to .epub-packaging will be retained
  --no-epubcheck   Disable the use of epubcheck to validate EPUBs
  --no-validate    Disable DTD validation of XML files during conversion. This
                   is only advised if you have pre-validated the files (see
                   'oaepub validate -h')

Logging Options:
  --no-log            Disable logging entirely
  -l --log=LOG        Specify a filepath to hold the log data
  --log-level=LEVEL   Set the level for the logging (one of: "CRITICAL",
                      "ERROR", "WARNING", "INFO", "DEBUG") [default: DEBUG]
  --echo-log          Log data will also be printed to console, at a level
                      determined by '--echo-level'
  --echo-level=LEVEL  Set the level of log data echoed to the console.
                      (one of: "CRITICAL", "ERROR", "WARNING", "INFO",
                      "DEBUG") [default: INFO]

Convert supports input of the following types:
  XML - Input points to the location of a local XML file (ends with: '.xml')
  DOI - A DOI to be resolved for XML download, if publisher is supported
        (starts with 'doi:')
  URL - A URL link to the article for XML download, if publisher is supported
        (starts with 'http:')

Each individual input will receive its own log (replace '.xml' with '.log')
unless '--log' is used to direct all logging information to a specific file
"""

#Standard Library modules
#import sys
#import os
import logging

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
import openaccess_epub.utils
import openaccess_epub.utils.log as oae_logging


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB Docoptify 0.1',
                  options_first=True)

    #Basic logging configuration
    if args['--no-log']:
        oae_logging.null_logging()  # Makes a log with a NullHandler
    else:
        oae_logging.config_logging(args['--log'],
                                   args['--log-level'],
                                   args['--echo-log'],
                                   args['--echo-level'])

    #Get a logger, this
    log = logging.getLogger('openaccess_epub.convert')

    #Our basic action is to iterate over the args['INPUT'] list
    for inpt in args['INPUT']:
        if inpt.lower().endswith('.xml'):  # This is direct XML file
            root_name = openaccess_epub.utils.file_root_name(inpt)
        #Otherwise, we have to download the file first
        elif inpt.lower().startswith('doi:'):  # This is a DOI
            pass
        elif inpt.lower().startswith('http:'):  # This is a URL
            pass

        #Set a new log file if a custom one has not been used
        if not args['--no-log'] and not args['--log']:
            log = logging.getLogger(name='openaccess_epub.convert')
            fh = logging.FileHandler(filename=root_name + '.log')
            fh.setFormatter(oae_logging.STANDARD_FORMAT)
            log.addHandler(fh)


if __name__ == '__main__':
    main()