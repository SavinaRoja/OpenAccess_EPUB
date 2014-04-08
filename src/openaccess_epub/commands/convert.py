# -*- coding: utf-8 -*-

"""
oaepub convert

Convert explicitly listed articles to EPUB, takes input of XML file, DOI, or URL

Usage:
  convert [--silent | --verbosity=LEVEL] [--epub2 | --epub3] [options] INPUT ...

General Options:
  -h --help             Show this help message and exit
  -v --version          Show program version and exit
  -s --silent           Print nothing to the console during execution
  -V --verbosity=LEVEL  Set how much information is printed to the console
                        during execution (one of: "CRITICAL", "ERROR",
                        "WARNING", "INFO", "DEBUG") [default: INFO]

Convert Specific Options:
  -2 --epub2            Convert to EPUB2
  -3 --epub3            Convert to EPUB3
  --no-cleanup          The EPUB contents prior to .epub-packaging will not be
                        removed
  --no-epubcheck        Disable the use of epubcheck to validate EPUBs
  --no-validate         Disable DTD validation of XML files during conversion.
                        This is only advised if you have pre-validated the files
                        (see 'oaepub validate -h')
  -o --output=DIR       Directory in which to put the output. Default is set in
                        config file (see 'oaepub configure where')
  -i --images=DIR       Directory in which to find the images for the article
                        to be converted to EPUB. If using this option with
                        multiple XML inputs, be sure to use wildcard filename
                        matching with a "*", which will expand to the filename
                        without extension. For more information and default
                        configuration see the config file
                        ('oaepub configure where')

Logging Options:
  --no-log-file         Disable logging to file
  -l --log-to=FILE      Specify a single filepath to contain all log data
  --log-level=LEVEL     Set the level for the logging (one of: "CRITICAL",
                        "ERROR", "WARNING", "INFO", "DEBUG") [default: DEBUG]

Convert supports input of the following types:
  XML - Input points to the location of a local XML file (ends with: '.xml')
  DOI - A DOI to be resolved for XML download, if publisher is supported
        (starts with 'doi:')
  URL - A URL link to the article for XML download, if publisher is supported
        (starts with 'http:' or 'https:')

Each individual input will receive its own log (replace '.xml' with '.log')
unless '--log-to' is used to direct all logging information to a specific file
Many default actions for your installation of OpenAccess_EPUB are configurable.
Execute 'oaepub configure' to interactively configure, or modify the config
file manually in a text editor; executing 'oaepub configure where' will tell you
where the config file is located.
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
from openaccess_epub.utils.epub import make_EPUB
import openaccess_epub.utils.images
import openaccess_epub.utils.inputs as input_utils
import openaccess_epub.utils.logs as oae_logging
from openaccess_epub.article import Article


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    if args['--epub3']:
        epub_version = 3
    elif args['--epub2']:
        epub_version = 2
    else:
        epub_version = None

    #Basic logging configuration
    oae_logging.config_logging(args['--no-log-file'],
                               args['--log-to'],
                               args['--log-level'],
                               args['--silent'],
                               args['--verbosity'])

    #Get a logger, the 'openaccess_epub' logger was set up above
    command_log = logging.getLogger('openaccess_epub.commands.convert')

    #Load the config module, we do this after logging configuration
    config = openaccess_epub.utils.load_config_module()

    current_dir = os.getcwd()
    #Our basic flow is to iterate over the args['INPUT'] list
    for inpt in args['INPUT']:
        #We have to temporarily re-base our log while input utils do some work
        if not args['--no-log-file'] and not args['--log-to']:
            oae_logging.replace_filehandler(logname='openaccess_epub',
                                            new_file='temp.log',
                                            level=args['--log-level'],
                                            frmt=oae_logging.STANDARD_FORMAT)

        command_log.info('Processing input: {0}'.format(inpt))

        #First we need to know the name of the file and where it is
        if inpt.lower().endswith('.xml'):  # This is direct XML file
            root_name = openaccess_epub.utils.file_root_name(inpt)
            abs_input_path = openaccess_epub.utils.get_absolute_path(inpt)
        elif inpt.lower().startswith('doi:'):  # This is a DOI
            root_name = input_utils.doi_input(inpt)
            abs_input_path = os.path.join(current_dir, root_name + '.xml')
        elif any(inpt.lower().startswith(i) for i in ['http:', 'https:']):
            root_name = input_utils.url_input(inpt)
            abs_input_path = os.path.join(current_dir, root_name + '.xml')
        else:
            sys.exit('{0} not recognized as XML, DOI, or URL'.format(inpt))

        if not args['--no-log-file'] and not args['--log-to']:
            log_name = root_name + '.log'
            log_path = os.path.join(os.path.dirname(abs_input_path), log_name)

            #Re-base the log file to the new file location
            oae_logging.replace_filehandler(logname='openaccess_epub',
                                            new_file=log_path,
                                            level=args['--log-level'],
                                            frmt=oae_logging.STANDARD_FORMAT)
            #Now we move over to the new log file
            shutil.copy2('temp.log', log_path)
            os.remove('temp.log')

        #Now that we should be done configuring logging, let's parse the article
        parsed_article = Article(abs_input_path,
                                 validation=not args['--no-validate'])

        if parsed_article.publisher is None:
            command_log.critical('Publisher support was not established, aborting')
            sys.exit(1)

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
                            epub_version=epub_version)

        #Cleanup removes the produced output directory, keeps the EPUB
        if not args['--no-cleanup']:
            command_log.info('Removing {0}'.format(output_directory))
            shutil.rmtree(output_directory)

        #Running epubcheck on the output verifies the validity of the EPUB,
        #requires a local installation of java and epubcheck.
        if not args['--no-epubcheck'] and success:
            epub_name = '{0}.epub'.format(output_directory)
            openaccess_epub.utils.epubcheck(epub_name, config)


if __name__ == '__main__':
    main()