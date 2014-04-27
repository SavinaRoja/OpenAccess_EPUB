# -*- coding: utf-8 -*-

"""
oaepub collection

Convert and compile a collection of article XML files into a single EPUB

Usage:
  collection [--silent | --verbosity=LEVEL] [--epub2 | --epub3] [options]
             COLLECTION_FILE

General Options:
  -h --help             Show this help message and exit
  -v --version          Show program version and exit
  -s --silent           Print nothing to the console during execution
  -V --verbosity=LEVEL  Set how much information is printed to the console
                        during execution (one of: "CRITICAL", "ERROR",
                        "WARNING", "INFO", "DEBUG") [default: INFO]

Collection Specific Options:
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

To prepare a collection, begin by ensuring that all required XMl files are
stored locally. Create a text file which contains a path to an XML file on
each line, in the order in which they should appear in the EPUB. The root name
of this text file will also serve as the name of the EPUB and the log (unless
the --log-to option is used).

If using the --images option, the argument should employ the "*" expansion. As
a precaution against wasting time, this command will quit if the "*" is missing.

Note: Metadata in a Collection EPUB is limited by necessity, not by mistake.
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
from openaccess_epub.navigation import Navigation
from openaccess_epub.package import Package
import openaccess_epub.utils as utils
from openaccess_epub.utils.epub import epub_zip, make_epub_base
import openaccess_epub.utils.images
import openaccess_epub.utils.logs as oae_logging
from openaccess_epub.article import Article


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    c_file = args['COLLECTION_FILE']
    c_file_root = utils.file_root_name(c_file)
    abs_input_path = utils.get_absolute_path(c_file)

    if not args['--log-to']:
        log_to = os.path.join(os.path.dirname(abs_input_path),
                              c_file_root + '.log')
    else:
        log_to = args['--log-to']

    #Basic logging configuration
    oae_logging.config_logging(args['--no-log-file'],
                               log_to,
                               args['--log-level'],
                               args['--silent'],
                               args['--verbosity'])

    command_log = logging.getLogger('openaccess_epub.commands.collection')

    #Load the config module, we do this after logging configuration
    config = openaccess_epub.utils.load_config_module()

    #Quit if the collection file is not there
    if not os.path.isfile(c_file):
        command_log.critical('File does not exist {0}'.format(c_file))
        sys.exit('Unable to continue')

    command_log.info('Parsing collection file: {0}'.format(c_file))
    with open(c_file, 'r') as f:
        inputs = [line.strip() for line in f.readlines()]

    #Get the output directory
    if args['--output'] is not None:
        output_directory = utils.get_absolute_path(args['--output'])
    else:
        if os.path.isabs(config.default_output):  # Absolute remains so
            output_directory = config.default_output
        else:  # Else rendered relative to input
            abs_dirname = os.path.dirname(abs_input_path)
            output_directory = os.path.normpath(os.path.join(abs_dirname, config.default_output))

    output_directory = os.path.join(output_directory, c_file_root)
    command_log.info('Processing collection output in {0}'.format(output_directory))

    if os.path.isdir(output_directory):
        utils.dir_exists(output_directory)
    try:
        os.makedirs(output_directory)
    except OSError as err:
        if err.errno != 17:
            command_log.exception('Unable to recursively create output directories')

    #Instantiate collection NCX and OPF
    navigation = Navigation(collection=True)
    package = Package(collection=True, title=c_file_root)

    #Copy over the basic epub directory
    make_epub_base(output_directory)

    epub_version = None

    #Iterate over the inputs
    for xml_file in inputs:
        xml_path = utils.evaluate_relative_path(os.path.dirname(abs_input_path),
                                                xml_file)
        parsed_article = Article(xml_path, validation=not args['--no-validate'])
        if epub_version is None:  # Only set this once, no mixing!
            if args['--epub2']:
                epub_version = 2
            elif args['--epub3']:
                epub_version = 3
            else:
                epub_version = parsed_article.publisher.epub_default

        navigation.process(parsed_article)
        package.process(parsed_article)

        #Get the Digital Object Identifier
        doi = parsed_article.get_DOI()
        journal_doi, article_doi = doi.split('/')

        #Get the images
        openaccess_epub.utils.images.get_images(output_directory,
                                                args['--images'],
                                                xml_path,
                                                config,
                                                parsed_article)

        parsed_article.publisher.render_content(output_directory, epub_version)

    if epub_version == 2:
        navigation.render_EPUB2(output_directory)
        package.render_EPUB2(output_directory)
    elif epub_version == 3:
        navigation.render_EPUB3(output_directory)
        package.render_EPUB3(output_directory)
    epub_zip(output_directory)

    #Cleanup removes the produced output directory, keeps the EPUB
    if not args['--no-cleanup']:
        command_log.info('Removing {0}'.format(output_directory))
        shutil.rmtree(output_directory)

    #Running epubcheck on the output verifies the validity of the ePub,
    #requires a local installation of java and epubcheck.
    if not args['--no-epubcheck']:
        epub_name = '{0}.epub'.format(output_directory)
        openaccess_epub.utils.epubcheck(epub_name, config)

if __name__ == '__main__':
    main()