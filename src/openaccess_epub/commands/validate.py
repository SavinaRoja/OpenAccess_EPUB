# -*- coding: utf-8 -*-

"""
oaepub validate

Validates XML files according to their DTD specification

Usage:
  validate [options] DIR ...

Options:
  -h --help             show this help message and exit
  -v --version          show program version and exit
  -s --silent           print nothing to the console during execution

Validate Specific Options:
  -l --log-to=LOG       Specify a location to store the log of DTD validation
  -p --print-only       Report output only to the console
  -P --record-pass      Keep records of XML files which pass DTD validation,
                        otherwise only the failures will be recorded
  -r --recursive        Recursively traverse subdirectories for validation

This command is especially useful for validating large numbers of XML files, so
that one can safely disable validation during repeated EPUB conversions of the
same XML files.

This command creates a single specialized log file within each directory given
as a DIR argument. This is true even with --recursive, a log will only be made
in the top level directory. This log will record which XML files failed (and
optionally, passed) validation along with the reason and details.
"""

#Standard Library modules
import logging
import os
import sys

#Non-Standard Library modules
from docopt import docopt
import lxml
import lxml.etree

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__
from openaccess_epub import JPTS10_PATH, JPTS11_PATH, JPTS20_PATH,\
    JPTS21_PATH, JPTS22_PATH, JPTS23_PATH, JPTS30_PATH
from openaccess_epub.utils import files_with_ext
import openaccess_epub.utils.logs as logs


DTDS = {'-//NLM//DTD Journal Archiving and Interchange DTD v1.0 20021201//EN': lxml.etree.DTD(JPTS10_PATH),
        '-//NLM//DTD Journal Archiving and Interchange DTD v1.1 20031101//EN': lxml.etree.DTD(JPTS11_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN': lxml.etree.DTD(JPTS20_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.1 20050630//EN': lxml.etree.DTD(JPTS21_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.2 20060430//EN': lxml.etree.DTD(JPTS22_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN': lxml.etree.DTD(JPTS23_PATH),
        '-//NLM//DTD Journal Publishing DTD v3.0 20080202//EN': lxml.etree.DTD(JPTS30_PATH)}


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    formatter = logging.Formatter('%(message)s')

    log = logging.getLogger('openaccess_epub.commands.validate')
    log.setLevel(logging.DEBUG)
    if not args['--silent']:
        sh_echo = logging.StreamHandler(sys.stdout)
        sh_echo.setLevel(logging.INFO)
        sh_echo.setFormatter(formatter)
        log.addHandler(sh_echo)

    for directory in args['DIR']:
        #Render the path to the directory
        if os.path.isabs(directory):
            dir_path = directory
        else:
            dir_path = os.path.normpath(os.path.join(os.getcwd(), directory))

        #Create the filename for the log
        if args['--log-to']:
            log_path = args['--log-to']
        else:
            logname = os.path.basename(dir_path) + '_validation.log'
            log_path = os.path.join(dir_path, logname)

        #Add the filehandler for the log if logging is enabled
        if not args['--print-only']:
            logs.replace_filehandler('openaccess_epub.commands.validate',
                                     new_file=log_path,
                                     level='INFO',
                                     frmt='%(message)s')

        #Iteration over the XML files
        for xml_file in files_with_ext('.xml', directory,
                                       recursive=args['--recursive']):
            try:
                document = lxml.etree.parse(xml_file)
            except lxml.etree.XMLSyntaxError as err:
                log.info('FAILED: Parse Error; {0} '.format(xml_file))
                log.info(str(err))
                continue

            #Find its public id so we can identify the appropriate DTD
            public_id = document.docinfo.public_id
            #Get the dtd by the public id
            try:
                dtd = DTDS[public_id]
            except KeyError as err:
                log.info('FAILED: Unknown DTD Error; {0}'.format(xml_file))
                log.info(str(err))

            #Actual DTD validation
            if not dtd.validate(document):
                log.info('FAILED: DTD Validation Error; {0}'.format(xml_file))
                log.info(str(dtd.error_log.filter_from_errors()))
                #Clear the error_log
                dtd._clear_error_log()
            else:
                if args['--record-pass']:
                    log.info('PASSED: Validated by DTD; {0}'.format(xml_file))


if __name__ == '__main__':
    main()