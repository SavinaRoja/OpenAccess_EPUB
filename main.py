#! /usr/bin/python

"""
This is the main execution file for OpenAccess_EPUB. It provides the primary
mode of execution and interaction.
"""

__version__ = '0.1.1'

#Standard Library Modules
import argparse
import sys
import os.path
import shutil
import urllib2
import urlparse
import logging

#OpenAccess_EPUB Modules
import utils
import opf
import tocncx
import opsfrontiers
import opsplos
import settings
from article import Article

settings = settings.Settings()


def OAEParser():
    """
    This function returns the parser args to the main method.
    """
    parser = argparse.ArgumentParser(description='OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version',
                        version='OpenAccess_EPUB {0}'.format(__version__))
    #parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-o', '--output', action='store',
                        default=settings.default_output,
                        help='Use to specify a desired output directory')
    parser.add_argument('-s', '--save-xml', action='store',
                        default=settings.xml_location,
                        help='''Use to specify a directory for storing \
                                downloaded xml files''')
    parser.add_argument('-l', '--log-to', action='store',
                        default=settings.log_location,
                        help='Use to specify a non-default log directory')
    parser.add_argument('-c', '--cache', action='store',
                        default=settings.cache_location,
                        help='Use to specify a non-default cache directory')
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


def initCache(cache_loc):
    """
    Initiates the cache if it does not exist
    """
    os.mkdir(cache_loc)
    os.mkdir(os.path.join(cache_loc, 'model'))
    os.mkdir(os.path.join(cache_loc, 'PLoS'))
    os.mkdir(os.path.join(cache_loc, 'Frontiers'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'figures'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'tables'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'equations'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'supplementary'))


def urlInput(inpt, xml_dir):
    """
    Handles input in URL form to instantiate the document. There is support for
    PLoS as well as some support for Frontiers. In order for it to work for
    Frontiers, the user must specify a link directly to the XML file.
    """
    try:
        if '%2F10.1371%2F' in inpt:  # This is a PLoS page
            address = urlparse.urlparse(inpt)
            _fetch = '/article/fetchObjectAttachment.action?uri='
            _id = address.path.split('/')[2]
            _rep = '&representation=XML'
            access = '{0}://{1}{2}{3}{4}'.format(address.scheme,
                                                 address.netloc,
                                                 _fetch, _id, _rep)
            print('Opening {0}'.format(access.__str__()))
            open_xml = urllib2.urlopen(access)
        elif 'www.frontiersin.org' in inpt:  # This is a Frontiers page
            try:
                open_xml = urllib2.urlopen(inpt)
                cd = open_xml.headers['Content-disposition']
                filename = cd.split('filename= ')[1]
            except:
                print('Unable to get the XML file or filename, make sure that \
you use a direct URL to the XML file.')
                sys.exit(1)
            else:
                filename = os.path.join(xml_dir, filename)
                with open(filename, 'wb') as xml_file:
                    xml_file.write(open_xml.read())
                document = Article(filename)
                return document, filename
        else:  # We don't know how to handle this input
            print('Invalid Link: Bad URL or unsupported publisher')
            sys.exit(1)
    except:
        sys.exit(1)
    else:
        filename = open_xml.headers['Content-disposition'].split('\"')[1]
        filename = os.path.join(xml_dir, filename)
        with open(filename, 'wb') as xml_file:
            xml_file.write(open_xml.read())
        document = Article(filename)
        return(document, filename)


def doiInput(inpt, xml_dir):
    """
    Handles input in DOI form to instantiate the document
    """
    try:
        doi_url = 'http://dx.doi.org/' + inpt[4:]
        page = urllib2.urlopen(doi_url)
        address = urlparse.urlparse(page.geturl())
        path = address.path.replace(':', '%3A').replace('/', '%2F')
        _fetch = '/article/fetchObjectAttachment.action?uri='
        _id = path.split('article%2F')[1]
        _rep = '&representation=XML'
        access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc,
                                    _fetch, _id, _rep)
        open_xml = urllib2.urlopen(access)
    except:
        print('Invalid DOI Link: Check for correct address and format')
        print('A valid entry looks like: \"doi:10.1371/journal.pcbi.1002222\"')
        sys.exit(1)
    else:
        filename = open_xml.headers['Content-Disposition'].split('\"')[1]
        filename = os.path.join(xml_dir, filename)
        with open(filename, 'wb') as xml_file:
            xml_file.write(open_xml.read())
        document = Article(filename)
        return(document, filename)


def localInput(inpt):
    """
    Handles input in the form of a local XML file to instantiate the document.
    """
    document = Article(inpt)
    return document


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
    if not os.path.isdir(settings.base_epub):
        utils.makeEPUBBase(settings.base_epub, settings.css_location)
    shutil.copytree(settings.base_epub, outdirect)
    DOI = document.getDOI()
    if DOI.split('/')[0] == '10.1371':  # PLoS's publisher DOI
        document.fetchPLoSImages(cache_dir, outdirect, settings.caching)
        opsplos.OPSPLoS(document, outdirect)
        toc = tocncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.PLoSOPF(__version__, outdirect, False)
    elif DOI.split('/')[0] == '10.3389':  # Frontiers' publisher DOI
        document.fetchFrontiersImages(cache_dir, outdirect, settings.caching)
        opsfrontiers.OPSFrontiers(document, outdirect)
        toc = tocncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.FrontiersOPF(__version__, outdirect, False)
    myopf.parseArticle(document)
    myopf.write()
    utils.epubZip(outdirect)
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be
    #taken whenever modifying this code
    #if settings.cleanup:
    #    shutil.rmtree(outdirect)


def makeCollectionEPUB(documents, cache_dir, outdirect, log_to):
    """"
    Encapsulates the processing workf-flow for the creation of
    \"collection\", or \"omnibus\" ePubs from multiple PLoS journal articles.
    Article objects have been instantiated and tupled to their local xml files
    and now we may generate the file.
    """
    print(u'Processing output to {0}.epub'.format(outdirect))
    shutil.copytree(settings.base_epub, outdirect)
    mytoc = tocncx.TocNCX(collection_mode=True)
    myopf = opf.ContentOPF(outdirect, collection_mode=True)
    for (doc, xml) in documents:
        DOI = doc.getDOI()
        doc.fetchPLoSImages(cache_dir, outdirect, settings.caching)
        content.OPSContent(xml, DOI, outdirect, doc)
        mytoc.takeArticle(doc)
        myopf.takeArticle(doc)
    mytoc.write(outdirect)
    myopf.write()
    utils.epubZip(outdirect)
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be
    #taken whenever modifying this code
    if settings.cleanup:
        shutil.rmtree(outdirect)


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
    #Certain directories must be in place in order to run. Here we check them.
    if not os.path.isdir(args.log_to):  # The logging directory
        os.mkdir(args.log_to)
    if not os.path.isdir(args.cache):  # The cache directory
        initCache(args.cache)
    if not os.path.isdir(args.save_xml):  # The directory for local XMLs
        os.mkdir(args.save_xml)
    if not os.path.isdir(args.output):  # The output directory
        os.mkdir(args.output)
    #Initiate logging settings
    logname = os.path.join(args.log_to, 'temp.log')
    logging.basicConfig(filename=logname, level=logging.DEBUG)
    logging.info('OpenAccess_EPUB Log v.{0}'.format(__version__))
    #Batch Mode
    if args.batch:
        download = False
        files = os.listdir(args.batch)
        for f in files:
            if not os.path.splitext(f)[1] == '.xml':
                pass
            else:
                filename = os.path.join(args.batch, f)
                xml_local = f
                doc = localInput(filename)
                input_name = os.path.splitext(os.path.split(xml_local)[1])[0]
                output_name = os.path.join(args.output, input_name)
                if os.path.isdir(output_name):
                    dirExists(output_name, args.batch)
                makeEPUB(doc, xml_local, args.cache, output_name, args.log_to)
        sys.exit(0)

    #Collection Mode
    if args.collection:
        t = os.path.splitext(os.path.split(args.collection)[1])[0]
        output_name = os.path.join(args.output, t)
        if os.path.isdir(output_name):
            dirExists(output_name, args.batch)
        with open(args.collection, 'r') as collection:
            inputs = collection.readlines()
        documents = []
        for i in inputs:
            if 'http://www' in i:
                download = True
                document, xml_local = urlInput(i.rstrip('\n'), args.save_xml)
            elif i[:4] == 'doi:':
                download = True
                document, xml_local = doiInput(i.rstrip('\n'), args.save_xml)
            else:
                if not i:
                    pass
                else:
                    download = False
                    document, xml_local = localInput(i.rstrip('\n'))
            documents += [(document, xml_local)]
        makeCollectionEPUB(documents, args.cache, output_name, args.log_to)
        epubcheck('{0}.epub'.format(output_name))
        sys.exit(0)

    #Single Input Mode
    else:
        #Determination of input type and processing
        if 'http://www' in args.input:
            download = True
            document, xml_local = urlInput(args.input, args.save_xml)
        elif args.input[:4] == 'doi:':
            download = True
            document, xml_local = doiInput(args.input, args.save_xml)
        else:
            download = False
            xml_local = args.input
            document = localInput(xml_local)
        #Later code versions may support the manual naming of the output file
        #as a commandline argument. For now, the name of the ePub file will be
        #the same as the input xml file.
        input_name = os.path.splitext(os.path.split(xml_local)[1])[0]
        output_name = os.path.join(args.output, input_name)
        if os.path.isdir(output_name):
            dirExists(output_name, args.batch)
        makeEPUB(document, xml_local, args.cache, output_name, args.log_to)
        if download and not settings.save_xml:
            os.remove(xml_local)
            newname = u'{0}.log'.format(input_name)
            newname = os.path.join(args.log_to, newname)
            os.rename(logname, newname)
        epubcheck('{0}.epub'.format(output_name))

if __name__ == '__main__':
    main()
