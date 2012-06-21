#! /usr/bin/python

"""
This is the main execution file for OpenAccess_EPUB. It provides the primary
mode of execution and interaction.
"""

#If you change the version here, make sure to also change it in setup.py
__version__ = '0.2.0'

#Standard Library Modules
import argparse
import sys
import os.path
import shutil
import logging

#OpenAccess_EPUB Modules
import utils.input
import opf
import ncx
import ops
import settings

settings = settings.Settings()


def OAEParser():
    """
    This function returns the parser args to the main method.
    """
    parser = argparse.ArgumentParser(description='OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version',
                        version='OpenAccess_EPUB {0}'.format(__version__))
    parser.add_argument('-o', '--output', action='store',
                        default=settings.local_output,
                        help='Use to specify a desired output directory')
    parser.add_argument('-l', '--log-to', action='store',
                        default=settings.local_log,
                        help='Use to specify a non-default log directory')
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


def makeEPUB(document, xml_local, cache_dir, outdirect, log_to):
    """
    Encapsulates the primary processing work-flow. Before this method is
    called, pre-processing has occurred to define important directory and file
    locations. The document has been processed for metadata and now it is time
    to generate the ePub content.
    """
    print(u'Processing output to {0}.epub'.format(outdirect))
    shutil.copytree(settings.base_epub, outdirect)
    DOI = document.getDOI()
    if DOI.split('/')[0] == '10.1371':  # PLoS's publisher DOI
        document.fetchPLoSImages(cache_dir, outdirect, settings.caching)
        ops.OPSPLoS(document, outdirect)
        toc = ncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.PLoSOPF(__version__, outdirect, False)
    elif DOI.split('/')[0] == '10.3389':  # Frontiers' publisher DOI
        document.fetchFrontiersImages(cache_dir, outdirect, settings.caching)
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
    os.execlp('java', 'OpenAccess_EPUB', '-jar', settings.epubcheck, epubname)


def main():
    """
    This is the main code execution block.
    """
    args = OAEParser()
    #Certain locations are defined by the user or by default for production
    #Here we make them if they don't already exist
    if not os.path.isdir(args.log_to):
        os.mkdir(args.log_to)
    if not os.path.isdir(args.output):
        os.mkdir(args.output)
    #The cache is a static directory which can hold various items
    #Image caching is of notable importance for some users.
    if not os.path.isdir(settings.cache_loc):
        utils.buildCache(settings.cache_loc)
    if not os.path.isdir(settings.xml_cache):
        os.mkdir(settings.xml_cache)
    if not os.path.isdir(settings.cache_log):
        os.mkdir(settings.cache_log)
    if not os.path.isdir(settings.cache_img):
        os.mkdir()
    #Single Input Mode
    #Determination of input type and processing
    if 'http://www' in args.input:
        download = True
        document, xml_local = utils.input.urlInput(args.input)
    elif args.input[:4] == 'doi:':
        download = True
        document, xml_local = utils.input.doiInput(args.input)
    else:
        download = False
        xml_local, document = utils.input.localInput(args.input)
    #Later code versions may support the manual naming of the output file
    #as a commandline argument. For now, the name of the ePub file will be
    #the same as the input xml file.
    input_name = os.path.splitext(os.path.split(xml_local)[1])[0]
    #Initiate logging settings
    logname = os.path.join(args.log_to, input_name + '.log')
    logging.basicConfig(filename=logname, level=logging.DEBUG)
    logging.info('OpenAccess_EPUB Log v.{0}'.format(__version__))
    #Generate the output name, the output directory + input_name
    output_name = os.path.join(args.output, input_name)
    if os.path.isdir(output_name):
        dirExists(output_name, args.batch)
    #Make the ePub!
    makeEPUB(document, xml_local, args.cache, output_name, args.log_to)
    #Everything after this point is post-handling. Place things in the cache
    #as appropriate and clean up.
    if settings.save_xml:
        shutil.copy2(xml_local, settings.xml_cache)
    if settings.save_log:
        shutil.copy2(logname, settings.cache_log)
    if settings.save_output:
        shutil.copy2(output_name, settings.cache_output)
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be
    #taken whenever modifying this code
    #if settings.cleanup:
    #    shutil.rmtree(output_name)
    epubcheck('{0}.epub'.format(output_name))

if __name__ == '__main__':
    main()
