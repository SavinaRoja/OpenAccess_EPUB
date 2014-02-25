# -*- coding: utf-8 -*-

"""
oaepub batch

Convert all XML files in a directory to individual EPUB files

Usage:
  batch [options] DIR ...

Options:
  -h --help             show this help message and exit
  -v --version          show program version and exit
  -s --silent           Print nothing to the console during execution
  -V --verbosity=LEVEL  Set how much information is printed to the console
                        during execution (one of: "CRITICAL", "ERROR",
                        "WARNING", "INFO", "DEBUG") [default: WARNING]

Batch Specific Options:
  -2 --epub2            Convert to EPUB2 (not implemented)
  -3 --epub3            Convert to EPUB3 (not implemented)
  --no-epubcheck        Disable the use of epubcheck to validate EPUBs
  --no-validate         Disable DTD validation of XML files during conversion.
                        This is only advised if you have pre-validated the files
                        (see 'oaepub validate -h')
  -r --recursive        Recursively traverse subdirectories for conversion
  -o --output=DIR       Directory in which to put the output. Default is set in
                        config file (see 'oaepub configure where')
  -i --images=DIR       Directory in which to find the images for the article
                        to be converted to EPUB. Be sure to use wildcard
                        filename matching with a "*", which will expand to the
                        filename without extension. For more information and
                        default configuration see the config file
                        ('oaepub configure where')

Logging Options:
  --no-log-file         Disable logging to file
  -l --log-to=FILE      Specify a single filepath to contain all log data
  --log-level=LEVEL     Set the level for the logging (one of: "CRITICAL",
                        "ERROR", "WARNING", "INFO", "DEBUG") [default: DEBUG]

In contrast to the 'convert' command, the 'batch' command is intended for larger
scale conversions of article XML to EPUB and is somewhat more specialized and
less flexible. Local XML files are the only allowed input, all directory
conflicts will result in the article being skipped (preventing overwrites), and
the command will attempt to convert all XML files in the specified directories.

If using the --images option, the argument should employ the "*" expansion. As
a precaution against wasting time, this command will quit if the "*" is missing.
"""

#Standard Library modules
import logging
import os
import shutil
import sys

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__
from openaccess_epub.utils import files_with_ext
from openaccess_epub.utils.epub import make_EPUB
import openaccess_epub.utils.images
import openaccess_epub.utils.logs as oae_logging
from openaccess_epub.article import Article


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    if args['--images'] is not None and '*' not in args['--images']:
        sys.exit('Argument for --images option must contain "*"')

    #Basic logging configuration
    oae_logging.config_logging(args['--no-log-file'],
                               args['--log-to'],
                               args['--log-level'],
                               args['--silent'],
                               args['--verbosity'])

    #Get a logger, the 'openaccess_epub' logger was set up above
    command_log = logging.getLogger('openaccess_epub.commands.batch')

    #Load the config module, we do this after logging configuration
    config = openaccess_epub.utils.load_config_module()

    for directory in args['DIR']:
        for xml_file in files_with_ext('.xml', directory,
                                       recursive=args['--recursive']):

            #We have to temporarily re-base our log while utils work
            if not args['--no-log-file']:
                oae_logging.replace_filehandler(logname='openaccess_epub',
                                                new_file='temp.log',
                                                level=args['--log-level'],
                                                frmt=oae_logging.STANDARD_FORMAT)

            command_log.info('Processing input: {0}'.format(xml_file))

            root_name = openaccess_epub.utils.file_root_name(xml_file)
            abs_input_path = openaccess_epub.utils.get_absolute_path(xml_file)

            if not args['--no-log-file']:
                log_name = root_name + '.log'
                log_path = os.path.join(os.path.dirname(abs_input_path),
                                        log_name)

                #Re-base the log file to the new file location
                oae_logging.replace_filehandler(logname='openaccess_epub',
                                                new_file=log_path,
                                                level=args['--log-level'],
                                                frmt=oae_logging.STANDARD_FORMAT)
                #Now we move over to the new log file
                shutil.move('temp.log', log_path)

            #Parse the article now that logging is ready
            parsed_article = Article(abs_input_path,
                                     validation=not args['--no-validate'])
            #Get the output directory
            if args['--output'] is not None:
                output_directory = openaccess_epub.utils.get_absolute_path(args['--output'])
            else:
                if os.path.isabs(config.default_output):  # Absolute remains so
                    output_directory = config.default_output
                else:  # Else rendered relative to input
                    abs_dirname = os.path.dirname(abs_input_path)
                    output_directory = os.path.normpath(os.path.join(abs_dirname, config.default_output))

            #The root name must be added on for output
            output_directory = os.path.join(output_directory, root_name)

            #Make the call to make_EPUB
            success = make_EPUB(parsed_article,
                                output_directory,
                                abs_input_path,
                                args['--images'],
                                config_module=config,
                                batch=True)

            #Cleanup is mandatory
            command_log.info('Removing {0}'.format(output_directory))
            shutil.rmtree(output_directory)

            if not args['--no-epubcheck'] and success:
                epub_name = '{0}.epub'.format(output_directory)
                openaccess_epub.utils.epubcheck(epub_name, config)


if __name__ == '__main__':
    main()