# -*- coding: utf-8 -*-

"""
oaepub configure

Configure some basic defaults for OpenAccess_EPUB

Usage:
  configure [options]

Options:
  -h --help        Show this help message and exit
  -v --version     Show program version and exit
  -d --default     Set configuration to default and exit
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