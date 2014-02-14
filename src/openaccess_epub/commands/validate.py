# -*- coding: utf-8 -*-

"""
oaepub validate

Validates XML files according to their DTD specification

Usage:
  validate [--log | [--print-only | --silent]] [options] DIR ...

Options:
  -h --help        show this help message and exit
  -v --version     show program version and exit
  -V --verbose     print extra information to the console during execution
  -s --silent      print nothing to the console during execution

Validate Specific Options:
  -l --log=LOG     Specify a location to store the log of DTD validation
  -p --print-only  Report output only to the console
  --record-pass    Record which XML files pass validation. Without this, only
                   failures will be recorded
  -r --recursive   Recursively traverse subdirectories for validation

This command is especially useful for validating large numbers of XML files, so
that one can safely disable validation during repeated EPUB conversions of the
same  XML files.

Regarding default log file creation behavior: each directory this command
conducts validation for will receive its own log file. The file will be receive
the name of the directory appended with '_validation.log'. If you want a single
log file with a user-specified name, use the '--log=LOG' option.
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