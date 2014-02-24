# -*- coding: utf-8 -*-

"""
oaepub validate

Validates XML files according to their DTD specification

Usage:
  validate [--log | [--print-only | --silent]] [options] DIR ...

Options:
  -h --help             show this help message and exit
  -v --version          show program version and exit
  -V --verbose          print extra information to the console during execution
  -s --silent           print nothing to the console during execution

Validate Specific Options:
  -l --log=LOG          Specify a location to store the log of DTD validation
  -p --print-only       Report output only to the console
  --record-pass         Keep records of XML files which pass DTD validation,
                        otherwise only the failures will be recorded
  -r --recursive        Recursively traverse subdirectories for validation
  -m --move-failed=DIR  All XML files which fail validation will be moved to DIR

This command is especially useful for validating large numbers of XML files, so
that one can safely disable validation during repeated EPUB conversions of the
same XML files.

Regarding default log file creation behavior: each directory this command
conducts validation for will receive its own log file. The file will be receive
the name of the directory appended with '_validation.log'. If you want a single
log file with a user-specified name, use the '--log=LOG' option.
"""

#Standard Library modules
import logging
import os
import shutil
import sys

#Non-Standard Library modules
from docopt import docopt
import lxml
import lxml.etree

#OpenAccess_EPUB modules
from openaccess_epub import JPTS10_PATH, JPTS11_PATH, JPTS20_PATH,\
    JPTS21_PATH, JPTS22_PATH, JPTS23_PATH, JPTS30_PATH
from openaccess_epub.utils import files_with_ext


DTDS = {'-//NLM//DTD Journal Archiving and Interchange DTD v1.0 20021201//EN': etree.DTD(JPTS10_PATH),
        '-//NLM//DTD Journal Archiving and Interchange DTD v1.1 20031101//EN': etree.DTD(JPTS11_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN': etree.DTD(JPTS20_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.1 20050630//EN': etree.DTD(JPTS21_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.2 20060430//EN': etree.DTD(JPTS22_PATH),
        '-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN': etree.DTD(JPTS23_PATH),
        '-//NLM//DTD Journal Publishing DTD v3.0 20080202//EN': etree.DTD(JPTS30_PATH)}


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB Docoptify 0.1',
                  options_first=True)

    #Basic logging configuration
    oae_logging.config_logging(args['--no-log-file'],
                               args['--log-to'],
                               args['--log-level'],
                               args['--silent'],
                               args['--verbosity'])

    log = logging.getLogger('openaccess_epub.commands.validate')

    for directory in args['DIR']:
        for xml_file in files_with_ext('.xml', directory,
                                       recursive=args['--recursive']):
            try:
                document = lxml.etree.parse(xml_file)
            except lxml.etree.XMLSyntaxError as err:
                if args['--move-failed']:
                    shutil.copy2(xml_file, os.path.join(args['--move-failed'], os.path.basename(xml_file))

            #Find its public id so we can identify the appropriate DTD
            public_id = document.docinfo.public_id
            #Get the dtd by the public id
            try:
                dtd = DTDS[public_id]
            except KeyError as err:
                #Add the file to the all_failed, noting as DTDError
                all_failed.write('DTDError: ' + xml_file + '\n')
                with open(os.path.splitext(xml_file)[0]+'.err', 'w') as err_file:
                    err_file.write(str(err))
                print('Document published according to unsupported specification. \
    Please contact the maintainers of OpenAccess_EPUB.')
            #Validate
            if not dtd.validate(document): # It failed
                #Add the name to all_failed
                all_failed.write(xml_file + '\n')
                with open(os.path.splitext(xml_file)[0]+'.err', 'w') as err_file:
                    err_file.write(str(dtd.error_log.filter_from_errors()))
                #Clear the error_log
                dtd._clear_error_log()
            else: # It passed
                #Nothing to do really
                pass
        #Close the all_failed file
        all_failed.close()


if __name__ == '__main__':
    main()