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
                        For more information and default configuration see the
                        config file ('oaepub configure where')

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
        (starts with 'http:')

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
import openaccess_epub
import openaccess_epub.utils
import openaccess_epub.utils.input as input_utils
import openaccess_epub.utils.logs as oae_logging
from openaccess_epub.article import Article


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
        elif inpt.lower().startswith('http:'):  # This is a URL
            root_name = input_utils.url_input(inpt)
            abs_input_path = os.path.join(current_dir, root_name + '.xml')
        else:
            sys.exit('{0} not recognized as XML, DOI, or URL'.format(inpt))

        if not args['--no-log-file'] and not args['--log-to']:
            log_name = root_name + '.log'
            log_path = os.path.join(os.path.dirname(abs_input_path), log_name)
            #Now we move over to the new log file
            shutil.move('temp.log', log_path)
            #And re-base the log file to the new file location
            oae_logging.replace_filehandler(logname='openaccess_epub',
                                            new_file=log_path,
                                            level=args['--log-level'],
                                            frmt=oae_logging.STANDARD_FORMAT)

        #Now that we should be done configuring logging, let's parse the article
        parsed_article = Article(abs_input_path,
                                 validation=not args['--no-validate'])

        #Get the output directory
        if args['--output'] is not None:
            output_directory = openaccess_epub.utils.get_absolute_path(args['--output'])
        else:
            output_directory = openaccess_epub.utils.get_absolute_path(config.default_output)

        #Call make_EPUB, the bread to our butter
        make_EPUB(parsed_article,
                  output_directory,
                  abs_input_path,
                  args['--images'],
                  config_module=config)


def make_EPUB(parsed_article,
              output_directory,
              input_path,
              image_directory,
              config_module=None):
    """
    make_EPUB is used to produce an EPUB file from a parsed article. In addition
    to the article it also requires a path to the appropriate image directory
    which it will insert into the EPUB file, as well the output directory
    location for the EPUB file.

    Parameters:
      article
          An Article object instance
      output_directory
          A directory path where the EPUB will be produced. The EPUB filename
          itself will always be
      input_path
          The absolute path to the input XML
      image_directory
          An explicitly indicated image directory, if used it will override the
          other image methods.
      config_module=None
          Allows for the injection of a modified or pre-loaded config module. If
          not specified, make_EPUB will load the config file
    """
    log.info('Creating {0}.epub'.format(output_directory))
    if config_module is None:
        config = openaccess_epub.utils.load_config_module()
    #Copy over the files from the base_epub to the new output
    if os.path.isdir(output_directory):
        openaccess_epub.utils.dir_exists(output_directory)

    #Copy over the basic epub directory
    base_epub = openaccess_epub.base_epub_location()
    shutil.copytree(base_epub, output_directory)

    DOI = parsed_article.doi

    #Get the images, if possible, fail gracefully if not
    success = openaccess_epub.utils.images.get_images(output_directory,
                                                      image_directory,
                                                      input_path,
                                                      config,
                                                      parsed_article)
    if not success:
        log.critical('Images for the article were not located! Aborting!')
        #I am not so bold as to call this without serious testing
        #shutil.rmtree(output_directory)

    epub_toc = openaccess_epub.ncx.NCX(openaccess_epub.__version__,
                                       output_directory)
    epub_opf = openaccess_epub.opf.OPF(output_directory,
                                       collection_mode=False)

    epub_toc.take_article(parsed_article)
    epub_opf.take_article(parsed_article)

    #Split now based on the publisher for OPS processing
    if DOI.split('/')[0] == '10.1371':  # PLoS
        epub_ops = openaccess_epub.ops.OPSPLoS(parsed_article,
                                               output_directory)
    elif DOI.split('/')[0] == '10.3389':  # Frontiers
        epub_ops = openaccess_epub.ops.OPSFrontiers(parsed_article,
                                                    output_directory)

    #Now we do the additional file writing
    epub_toc.write()
    epub_opf.write()

    #Zip the directory into EPUB
    openaccess_epub.utils.epub_zip(output_directory)


if __name__ == '__main__':
    main()