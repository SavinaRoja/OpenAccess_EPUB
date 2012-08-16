#! /usr/bin/python

"""
This is the main execution file for OpenAccess_EPUB. It provides the primary
mode of execution and interaction.
"""

#If you change the version here, make sure to also change it in setup.py and
#the module __init__.py
__version__ = '0.2.3'

#Standard Library Modules
import argparse
import sys
import os.path
import shutil
import logging

#OpenAccess_EPUB Modules
import utils.input
import utils.images
import opf
import ncx
import ops
import settings

setngs = settings.Settings()
log = logging.getLogger('Main')


def OAEParser():
    """
    This function returns the parser args to the main method.
    """
    parser = argparse.ArgumentParser(description='OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version',
                        version='OpenAccess_EPUB {0}'.format(__version__))
    parser.add_argument('-o', '--output', action='store',
                        default=setngs.local_output,
                        help='Use to specify a desired output directory')
    parser.add_argument('-l', '--log-to', action='store',
                        default=setngs.local_log,
                        help='Use to specify a non-default log directory')
    parser.add_argument('-I', '--images', action='store',
                        default=setngs.default_images,
                        help='''Specify a path to the directory containing the
                        images. This overrides the program's attempts to get
                        the images from the default directory, the image cache,
                        or the internet.''')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('-i', '--input', action='store',
                        help='''Input may be a path to a local directory, a \
                              URL to a PLoS journal article, or a PLoS DOI \
                              string''')
    modes.add_argument('-b', '--batch', action='store', default=False,
                        help='''Use to specify a batch directory; each \
                                article inside will be processed.''')
    modes.add_argument('-C', '--collection', action='store', default=False,
                        help='''Use to create an ePub file containing \
                                multiple resources.''')
    modes.add_argument('-cI', '--clear-image-cache', action='store_true',
                       default=False, help='''Clears the image cache''')
    modes.add_argument('-cX', '--clear-xml-cache', action='store_true',
                       default=False, help='''Clears the xml cache''')
    modes.add_argument('-cC', '--clear-cache', action='store_true',
                       default=False, help='''Clears the entire cache''')
    return parser.parse_args()


def dirExists(outdirect, batch):
    """
    Provides interaction with the user if the output directory already exists.
    If running in batch mode, this interaction is ignored and the directory
    is automatically deleted.
    """
    if not batch:
        print(u'The directory {0} already exists.'.format(outdirect))
        r = raw_input('Replace? [y/n]')
        if r in ['y', 'Y', '']:
            shutil.rmtree(outdirect)
        else:
            print('Aborting process.')
            sys.exit()
    else:
        shutil.rmtree(outdirect)


def makeEPUB(document, xml_local, outdirect, images):
    """
    Encapsulates the primary processing work-flow. Before this method is
    called, pre-processing has occurred to define important directory and file
    locations. The document has been processed for metadata and now it is time
    to generate the ePub content.
    """
    print(u'Processing output to {0}.epub'.format(outdirect))
    shutil.copytree(setngs.base_epub, outdirect)
    DOI = document.getDOI()
    utils.images.localImages(images, outdirect, DOI)
    #utils.images.getImages(DOI, images, outdirect, setngs.default_images,
    #                       setngs.caching, setngs.cache_img)
    if DOI.split('/')[0] == '10.1371':  # PLoS's publisher DOI
        #document.fetchPLoSImages(cache_dir, outdirect, setngs.caching)
        ops.OPSPLoS(document, outdirect)
        toc = ncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.PLoSOPF(__version__, outdirect, False)
    elif DOI.split('/')[0] == '10.3389':  # Frontiers' publisher DOI
        #document.fetchFrontiersImages(cache_dir, outdirect, setngs.caching)
        ops.OPSFrontiers(document, outdirect)
        toc = ncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.FrontiersOPF(__version__, outdirect, False)
    myopf.parseArticle(document)
    myopf.write()
    utils.epubZip(outdirect)


def epubcheck(epubname):
    """
    This method takes the name of an epub file as an argument. This name is
    the input for the java execution of a locally installed epubcheck-.jar. The
    location of this .jar file is configured in settings.py.
    """
    r, e = os.path.splitext(epubname)
    if not e:
        print('Warning: Filename extension is empty, appending \'.epub\'...')
        e = '.epub'
        epubname = r + e
    elif not e == '.epub':
        print('Warning: Filename extension is not \'.epub\', appending it...')
        epubname += '.epub'
    os.execlp('java', 'OpenAccess_EPUB', '-jar', setngs.epubcheck, epubname)


def main(args, temp_log_id, temp_log_path):
    """
    This is the main code execution block.
    """
    #Certain locations are defined by the user or by default for production
    #Here we make them if they don't already exist
    if not os.path.isdir(args.log_to):
        os.mkdir(args.log_to)
    if not os.path.isdir(args.output):
        os.mkdir(args.output)
    #The cache is a static directory which can hold various items
    #Image caching is important for some users.
    if not os.path.isdir(setngs.cache_loc):
        utils.buildCache(setngs.cache_loc)
    if not os.path.isdir(setngs.xml_cache):
        os.mkdir(setngs.xml_cache)
    if not os.path.isdir(setngs.cache_log):
        os.mkdir(setngs.cache_log)
    if not os.path.isdir(setngs.cache_img):
        utils.images.initImgCache(setngs.cache_img)
    if not os.path.isdir(setngs.base_epub):
        utils.makeEPUBBase(setngs.base_epub)
    #Single Input Mode
    #Determination of input type and processing
    if 'http://www' in args.input:
        document, xml_local = utils.input.urlInput(args.input)
    elif args.input[:4] == 'doi:':
        document, xml_local = utils.input.doiInput(args.input)
    else:
        xml_local, document = utils.input.localInput(args.input)
    #Later code versions may support the manual naming of the output file
    #as a commandline argument. For now, the name of the ePub file will be
    #the same as the input xml file.
    input_name = os.path.splitext(os.path.split(xml_local)[1])[0]
    #Set the log name
    logname = os.path.join(args.log_to, input_name + '.log')
    os.close(temp_log_id)
    os.rename(temp_log_path, logname)
    #Generate the output name, the output directory + input_name
    output_name = os.path.join(args.output, input_name)
    if os.path.isdir(output_name):
        dirExists(output_name, args.batch)

    #Make the ePub!
    makeEPUB(document,  # The parsed Article class
             xml_local,  # The path to the local xml file
             output_name,  # The name of the output file
             args.images)  # Path specifying where to find the images

    #Everything after this point is post-handling. Place things in the cache
    #as appropriate and clean up.
    if setngs.save_xml:
        shutil.copy2(xml_local, setngs.xml_cache)
    if setngs.save_log:
        shutil.copy2(logname, setngs.cache_log)
    if setngs.save_output:
        shutil.copy2(output_name, setngs.cache_output)
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be
    #taken whenever modifying this code
    #if setngs.cleanup:
    #    shutil.rmtree(output_name)
    epubcheck('{0}.epub'.format(output_name))
