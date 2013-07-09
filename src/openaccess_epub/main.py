# -*- coding: utf-8 -*-

"""
This is the main execution file for OpenAccess_EPUB. It provides the primary
mode of execution and interaction.
"""

#Standard Library Modules
import argparse
import sys
import os
import shutil
import logging
import traceback
import subprocess

#OpenAccess_EPUB Modules
from ._version import __version__
import openaccess_epub.utils as utils
import openaccess_epub.utils.input as u_input
from openaccess_epub.utils.images import get_images
import openaccess_epub.opf as opf
import openaccess_epub.ncx as ncx
import openaccess_epub.ops as ops
from openaccess_epub.article import Article

CACHE_LOCATION = utils.cache_location()
LOCAL_DIR = os.getcwd()

log = logging.getLogger('Main')

def OAEParser():
    """
    This function returns the parser args to the main method.
    """
    parser = argparse.ArgumentParser(description='OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version',
                        version='OpenAccess_EPUB {0}'.format(__version__))
    parser.add_argument('-o', '--output', action='store',
                        default=None,
                        help='''Specify a non-default directory for the
                        placement of output.''')
    parser.add_argument('-I', '--images', action='store',
                        default=None,
                        help='''Specify a path to the directory containing the
                        images. This overrides the program's attempts to get
                        the images from the input-relative directory, the image
                        cache, or the Internet.''')
    parser.add_argument('-c', '--clean', action='store_true', default=False,
                        help='''Use to toggle on cleanup. With this flag,
                                the pre-zipped output will be removed.''')
    parser.add_argument('-e', '--no-epubcheck', action='store_false',
                        default=True,
                        help='''Use this to skip ePub validation by EpubCheck.''')
    parser.add_argument('-d', '--no-dtd-validation', action='store_false',
                        default=True,
                        help='''Use this to skip DTD-validation on the input
                                file(s). This is advised only for use on files
                                that have already been validated by dtdvalidate
                                or otherwise.''')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('-i', '--input', action='store', default=False,
                       help='''Input may be a path to a local directory, a
                              URL to a PLoS journal article, or a PLoS DOI
                              string''')
    modes.add_argument('-z', '--zip', action='store', default=False,
                       help='''Input mode supporting Frontiers production from
                               zipfiles. Use the name of either of the zipfiles
                               with this mode, both zipfiles are required to be
                               in the same directory.''')
    modes.add_argument('-b', '--batch', action='store', default=False,
                       help='''Use to specify a batch directory; each
                               article inside will be processed.''')
    modes.add_argument('-p', '--parallel-batch', action='store', default=False,
                       help='''Use to specify a batch directory for parallel
                               processing.''')
    modes.add_argument('-C', '--collection', action='store', default=False,
                       nargs='?', const=True,
                       help='''Use to combine all xml files in the local
                               directory into a single ePub collection.
                               Typing a string after this flag will provide a
                               title for the collection. If no title is given,
                               the main script may ask for one.''')
    modes.add_argument('-cI', '--clear-image-cache', action='store_true',
                       default=False, help='''Clears the image cache''')
    modes.add_argument('-cC', '--clear-cache', action='store_true',
                       default=False, help='''Clears the entire cache''')
    return parser.parse_args()


def dir_exists(outdirect):
    """
    Provides interaction with the user if the output directory already exists.
    If running in batch mode, this interaction is ignored and the directory
    is automatically deleted.
    """
    print('The directory {0} already exists.'.format(outdirect))
    r = input('Replace? [Y/n]')
    if r in ['y', 'Y', '']:
        shutil.rmtree(outdirect)
    else:
        sys.exit('Aborting process!')

def single_input(args, config=None):
    """
    Single Input Mode works to convert a single input XML file into EPUB.

    This is probably the most typical use case and is the most highly
    configurable, see the argument parser and oaepub --help
    """
    if config is None:
        config = get_config_module()
    #Determination of input type and processing
    #Fetch by URL
    if 'http:' in args.input:
        raw_name = u_input.url_input(args.input)
        abs_input_path = os.path.join(LOCAL_DIR, raw_name+'.xml')
        parsed_article = Article(abs_input_path, validation=args.no_dtd_validation)
    #Fetch by DOI
    elif args.input[:4] == 'doi:':
        raw_name = u_input.doi_input(args.input)
        abs_input_path = os.path.join(LOCAL_DIR, raw_name+'.xml')
        parsed_article = Article(abs_input_path, validation=args.no_dtd_validation)
    #Local XML input
    else:
        abs_input_path = utils.get_absolute_path(args.input)
        raw_name = u_input.local_input(abs_input_path)
        parsed_article = Article(abs_input_path, validation=args.no_dtd_validation)

    #Generate the output path name, this will be the directory name for the
    #output. This output directory will later be zipped into an EPUB
    output_name = os.path.join(utils.get_output_directory(args), raw_name)

    #Make the EPUB
    make_epub(parsed_article,
              outdirect=output_name,
              explicit_images=args.images,   # Explicit image path
              batch=False,
              config=config)

    #Cleanup removes the produced output directory, keeps the ePub file
    if args.clean:  # Defaults to False, --clean or -c to toggle on
        shutil.rmtree(output_name)

    #Running epubcheck on the output verifies the validity of the ePub,
    #requires a local installation of java and epubcheck.
    if args.no_epubcheck:
        epubcheck('{0}.epub'.format(output_name), config)


def batch_input(args, config=None):
    """
    Batch Input Mode works to convert all of the article XML files in a
    specified directory into individual article EPUB files.

    Batch Input Mode is employed under a few simplifying assumptions: any
    pre-existing folder for article EPUB conversion will be eliminated without
    asking user permission, all output that except the .epub and .log files
    will be removed, and image files in a custom directory are not being used.

    Unlike the other input modes, Batch Input Mode output is always relative to
    the batch directory rather than the working directory of oaepub execution.

    Batch Input Mode has default epubcheck behavior, it will place a system
    call to epubcheck unless specified otherwise (--no-epubcheck or -N flags).
    """
    if config is None:
        config = get_config_module()
    error_file = open('batch_tracebacks.txt', 'w')
    #Iterate over all listed files in the batch directory
    for item in os.listdir(args.batch):
        item_path = os.path.join(args.batch, item)
        #Skip directories and files without .xml extension
        _root, extension = os.path.splitext(item)
        if not os.path.isfile(item_path):
            continue
        if not extension == '.xml':
            continue
        print(item_path)

        #Parse the article
        try:
            raw_name = u_input.local_input(item_path)
        except:
            traceback.print_exc(file=error_file)
        else:
            parsed_article = Article(os.path.join(args.batch, raw_name+'.xml'),
                                     validation=args.no_dtd_validation)

        #Create the output name
        output_name = os.path.join(utils.get_output_directory(args), raw_name)

        #Make the EPUB
        try:
            make_epub(parsed_article,
                      outdirect=output_name,
                      explicit_images=None,   # No explicit image path
                      batch=True,
                      config=config)
        except:
            error_file.write(item_path + '\n')
            traceback.print_exc(file=error_file)

        #Cleanup output directory, keeps EPUB and log
        shutil.rmtree(output_name)

        #Running epubcheck on the output verifies the validity of the ePub,
        #requires a local installation of java and epubcheck.
        if args.no_epubcheck:
            epubcheck('{0}.epub'.format(output_name), config)
    error_file.close()


def collection_input(args, config=None):
    """
    Collection Input Mode works to compile multiple articles into a single
    composite ePub. This is akin to such formats as Collections, Issues, and
    Omnibus; it may also be useful for those interested in the simple
    distribution of a reading list, personal publications, or topic reference.

    Collection Input Mode produces output that is necessarily unlike the output
    generated by Single or Batch (which is just sequential Single) input modes.
    The primary difference in output lies with the ePub metadata; as applying
    metadata from any single article to the whole would be inappropriate.

    Unlike other input modes, Collection Mode is strictly dependent on the
    local directory of execution. If there is a file named "order.txt" in the
    local directory, this file should contain the name of one input XML file
    on each line; the files will be added to the ePub output by line-order.
    If there is "order.txt" file, Collection Mode will assume that all XML
    files are input and the article in order in the collection will be random.

    Collection Input Mode has default epubcheck behavior, it will place a system
    call to epubcheck unless specified otherwise (--no-epubcheck or -N flags).
    """
    if config is None:
        config = get_config_module()
    try:
        order = open('order.txt', 'r')
    except IOError:  # No order.txt
        xml_files = list_xml_files(dir=os.getcwd())
    else:
        #Add all nonempty lines, in order, to the xml_files list
        xml_files = [i.strip() for i in order.readlines() if i.strip()]
        order.close()

    #The output name will be the same as the parent directory name
    #This will also serve as the dc:title
    output_name = os.path.split(os.getcwd())[1]

    #The standard make_epub() method will not work for Collection Mode
    #So the work done here is an adaptation of it
    print('Processing output to {0}.epub'.format(output_name))
    #Copy files from base_epub to the new output
    if os.path.isdir(output_name):
        dir_exists(output_name)
    epub_base = os.path.join(CACHE_LOCATION, 'base_epub')
    shutil.copytree(epub_base, output_name)

    if args.collection is True:
        try:
            title_txt = open('title.txt', 'r')
        except IOError:  # No title.txt
            title = output_name
        else:
            title = title_txt.readline().strip()
            title_txt.close()
            if not title:
                title = output_name
                print('title.txt was empty or title was not on first line!')
                print('Defaulting to name of parent directory. {0}'.format(title))
    else:
        title = args.collection
    
    toc = ncx.NCX(oae_version=__version__, location=output_name, collection_mode=True)
    myopf = opf.OPF(location=output_name, collection_mode=True, title=title)
    
    #Now it is time to operate on each of the xml files
    for xml_file in xml_files:
        raw_name = u_input.local_input(xml_file)  # is this used?
        parsed_article = Article(xml_file, validation=args.no_dtd_validation)
        toc.take_article(parsed_article)
        myopf.take_article(parsed_article)
    
        if parsed_article.metadata.dtdVersion() == '2.0':  #Not supported
            print('Article published with JPTS DTDv2.0, not supported!')
            sys.exit(1)
        #Get the Digital Object Identifier
        doi = parsed_article.get_DOI()
        journal_doi, article_doi = doi.split('/')
        
        #Check for images
        img_dir = os.path.join(output_name, 'OPS', 'images-{0}'.format(article_doi))
        expected_local = 'images-{0}'.format(raw_name)
        if os.path.isdir(expected_local):
            utils.images.local_images(expected_local, img_dir)
        else:
            article_cache = os.path.join(config.image_cache, journal_doi, article_doi)
            if os.path.isdir(article_cache):
                utils.images.image_cache(article_cache, img_dir)
            else:
                print('Images for {0} (DOI: {1}) could not be found!'.format(xml_file, doi))
                r = input('Try to download them? [Y/n]')
                if r in ['y', 'Y', '']:
                    os.mkdir(img_dir)
                    utils.images.fetch_plos_images(article_doi, img_dir, parsed_article)
                    if config.use_image_cache:
                        utils.images.move_images_to_cache(img_dir, article_cache)
                else:
                    sys.exit(1)

        #TODO: Content stuff
        if journal_doi == '10.1371':  # PLoS's publisher DOI
            ops_doc = ops.OPSPLoS(parsed_article, output_name)
            #TODO: Workflow change, parse table of contents from OPS processed document
            
    toc.write()
    myopf.write()
    utils.epub_zip(output_name)
    

    #Running epubcheck on the output verifies the validity of the ePub,
    #requires a local installation of java and epubcheck.
    if args.no_epubcheck:
        epubcheck('{0}.epub'.format(output_name), config)


def zipped_input(args, config=None):
    """
    Zipped Input Mode is primarily intended as a workflow for Frontiers
    articles, where the article xml and relevant images are zipped together.
    """
    if config is None:
        config = get_config_module()


def make_epub(article, outdirect, explicit_images, batch, config=None):
    """
    Encapsulates the primary processing work-flow. Before this method is
    called, pre-processing has occurred to define important directory and file
    locations. The article has been processed for metadata and now it is time
    to generate the ePub content.
    """
    print('Processing output to {0}.epub'.format(outdirect))
    if config is None:
        config = get_config_module()
    #Copy files from base_epub to the new output
    if os.path.isdir(outdirect):
        if batch:
            shutil.rmtree(outdirect)
        else:
            dir_exists(outdirect)
    epub_base = os.path.join(CACHE_LOCATION, 'base_epub')
    shutil.copytree(epub_base, outdirect)

    #Get the Digital Object Identifier
    DOI = article.get_DOI()

    #Get the images
    get_images(DOI, outdirect, explicit_images, config, article)

    toc = ncx.NCX(__version__, outdirect)
    myopf = opf.OPF(outdirect, False)
    toc.take_article(article)
    myopf.take_article(article)
    ops_doc = ops.OPSPLoS(article, outdirect)
    toc.write()
    myopf.write()
    utils.epub_zip(outdirect)


def epubcheck(epubname, config=None):
    """
    This method takes the name of an epub file as an argument. This name is
    the input for the java execution of a locally installed epubcheck-.jar. The
    location of this .jar file is configured in config.py.
    """
    if config is None:
        config = get_config_module()
    r, e = os.path.splitext(epubname)
    if not e:
        print('Warning: Filename extension is empty, appending \'.epub\'...')
        e = '.epub'
        epubname = r + e
    elif not e == '.epub':
        print('Warning: Filename extension is not \'.epub\', appending it...')
        epubname += '.epub'
    subprocess.call(['java', '-jar', config.epubcheck, epubname])

def get_config_module():
    """
    If the config.py file exists, import it as a module. If it does not exist,
    call sys.exit() to quit.
    """
    #Import the global config file as a module
    import imp
    config_path = os.path.join(CACHE_LOCATION, 'config.py')
    try:
        config = imp.load_source('config', config_path)
    except IOError:
        print('Could not find {0}, please run oae-quickstart'.format(config_path))
        sys.exit(1)
    else:
        return config


def list_xml_files(dir):
    """
    Receives a path to a system directory and then returns a list of all XML
    files contained in the directory.
    """
    xml_files = []
    for item in os.listdir(dir):
        item_path = os.path.join(dir, item)
        #Skip directories and files without .xml extension
        _root, extension = os.path.splitext(item_path)
        if os.path.isfile(item_path) and extension == '.xml':
            xml_files.append(item_path)
    return xml_files

def main(args):
    """
    This is the main code execution block.
    """

    #Make sure that the base_epub is in place
    utils.make_epub_base()  # Static location
    
    #Import the config module, this fails and exits if it does not exist
    config = get_config_module()
    
    #Even if they don't plan on using the image cache, make sure it exists
    utils.images.make_image_cache(config.image_cache)  # User configurable

    #Make appropriate calls depending on input type
    #These are all mutually exclusive arguments in the argument parser
    if args.input:  # Convert single article to EPUB
        single_input(args, config)
    elif args.batch:  # Convert large numbers of XML files to EPUB
        batch_input(args, config)
    elif args.parallel_batch:  # Convert large numbers of XML files to EPUB in parallel
        parallel_batch_input(args, config)
    elif args.collection:  # Convert multiple XML articles into single EPUB
        collection_input(args, config)
    elif args.zipped:  # Convert Frontiers zipfile into single EPUB
        zipped_input(args, config)
