# -*- coding: utf-8 -*-

"""
oaepub convert

Convert explicitly listed articles to EPUB, takes input of XML file, DOI, or URL

Usage:
  convert [--silent | --log-echo] [options] INPUT ...

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
    --log-echo          Log data will also be printed to console, at a level
                        determined by '--echo-level'
    --echo-level=LEVEL  Set the level of log data echoed to the console.
                        (one of: "CRITICAL", "ERROR", "WARNING", "INFO",
                        "DEBUG") [default: DEBUG]

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
import sys
#import os
import logging

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
import openaccess_epub.utils


def null_logging():
    log = logging.getLogger('openaccess_epub')
    log.addHandler(logging.NullHandler())


def config_logging(log_to, log_level, log_echo, echo_level):
    """
    Configures and generates a Logger object based on common parameters used for
    console script execution in OpenAccess_EPUB.

    These parameters are:
      log_to - Defines a log file location, if False, filename will not be set
      log_level - Defines the logging level
      log_echo - If True, log data will also print to console
      echo_level - Defines the logging level of console-printed data

    This function assumes it will only be called when logging is desired; it
    should not be called if an option such as '--no-log' is used.
    """

    levels = {'debug': logging.DEBUG, 'info': logging.INFO,
              'warning': logging.WARNING, 'error': logging.ERROR,
              'critical': logging.CRITICAL}

    try:
        log_level = levels[log_level.lower()]
        echo_level = levels[echo_level.lower()]
    except KeyError:
        sys.exit('{0} is not a recognized logging level')
    else:
        log = logging.getLogger('openaccess_epub')
        log.setLevel(log_level)
        frmt = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        if log_to:
            fh = logging.FileHandler(filename=log_to)
            fh.setFormatter(frmt)
            log.addHandler(fh)
        #Add on the console StreamHandler if we are echoing to console
        if log_echo:
            sh_echo = logging.StreamHandler(sys.stdout)
            sh_echo.setLevel(echo_level)
            sh_echo.setFormatter(frmt)
            log.addHandler(sh_echo)


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

    #Basic logging configuration, if appropriate
    if args['--no-log']:
        null_logging()
    else:
        config_logging(args['--log'],
                       args['--log-level'],
                       args['--log-echo'],
                       args['--echo-level'])
    log = logging.getLogger('openaccess_epub.convert')
    log.debug('Hello Log World!')

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
            log.addHandler(logging.FileHandler(filename=root_name + '.log'))

        #log.debug('Hello Log World!')


if __name__ == '__main__':
    main()