#! /usr/bin/python

__version__ = '0.0.8'

#Standard Library Modules
import argparse
import sys
import os.path
import shutil
import urllib2
import urlparse
import logging
import datetime

#OpenAccess_EPUB Modules
import utils
import metadata
import opf
import tocncx
import content
from settings import Settings
from article import Article

settings = Settings()

def initCache(cache_loc):
    '''Initiates the cache if it does not exist'''
    os.mkdir(cache_loc)
    os.mkdir(os.path.join(cache_loc, 'model'))
    os.mkdir(os.path.join(cache_loc, 'PLoS'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'figures'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'tables'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'equations'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'supplementary'))

def urlInput(input, xml_dir):
    '''Handles input in URL form to instantiate the document'''
    try:
        address = urlparse.urlparse(input)
        _fetch = '/article/fetchObjectAttachment.action?uri='
        _id = address.path.split('/')[2]
        _rep = '&representation=XML'
        access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc, 
                                    _fetch, _id, _rep)
        print(access)
        open_xml = urllib2.urlopen(access)
        
    except:
        print('Invalid Link: Enter a corrected link or use local file')
        sys.exit(1)
    
    else:
        filename = open_xml.headers['Content-disposition'].split('\"')[1]
        filename = os.path.join(xml_dir, filename)
        with open(filename, 'wb') as xml_file:
            xml_file.write(open_xml.read())
        document = Article(filename)
        return(document, filename)

def doiInput(input, xml_dir):
    '''Handles input in DOI form to instantiate the document'''
    try:
        doi_url = 'http://dx.doi.org/' + input[4:]
        page = urllib2.urlopen(doi_url)
        address = urlparse.urlparse(page.geturl())
        _fetch = '/article/fetchObjectAttachment.action?uri='
        _id = address.path.split('/')[2]
        _rep = '&representation=XML'
        access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc, 
                                    _fetch, _id, _rep)
        open_xml = urllib2.urlopen(access)
        
    except:
        print('Invalid DOI Link: Make sure that the address and format are correct')
        print('A valid entry looks like: \"doi:10.1371/journal.pcbi.1002222\"')
        sys.exit(1)
    
    else:
        filename = open_xml.headers['Content-Disposition'].split('\"')[1]
        filename = os.path.join(xml_dir, filename)
        with open(filename, 'wb') as xml_file:
            xml_file.write(open_xml.read())
        document = Article(filename)
        return(document, filename)

def localInput(input):
    '''Handles input in the form of local file to instantiate the document'''
    xml_local = input
    document = Article(xml_local)
    return(document, xml_local)

def dirExists(outdirect, batch):
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
    '''
    Encapsulates the primary processing work-flow. Before this method is 
    called, pre-processing has occurred to define important directory and file 
    locations. The document has been processed for metadata and now it is time 
    to generate the ePub content.
    '''
    print(u'Processing output to {0}.epub'.format(outdirect))
    if not os.path.isdir(settings.base_epub):
        utils.makeEPUBBase(settings.base_epub, settings.css_location)
    shutil.copytree(settings.base_epub, outdirect)
    DOI = document.getDOI()
    utils.fetchPLoSImages(DOI, cache_dir, outdirect, settings.caching)
    content.OPSContent(xml_local, DOI, outdirect, document.front, document.back)
    toc = tocncx.TocNCX()
    toc.takeArticle(document)
    toc.write(outdirect)
    opf.generateOPF(document, outdirect)
    utils.epubZip(outdirect)
    
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be 
    #taken whenever modifying this code
    if settings.cleanup:
        shutil.rmtree(outdirect)
    
def makeCollectionEPUB(documents, cache_dir, outdirect, log_to):
    '''Encapsulates the processing workf-flow for the creation of 
    \"collection\", or \"omnibus\" ePubs from multiple PLoS journal articles. 
    Article objects have been instantiated and tupled to their local xml files 
    and now we may generate the file.
    '''
    print(u'Processing output to {0}.epub'.format(outdirect))
    shutil.copytree(settings.base_epub, outdirect)
    mytoc = tocncx.TocNCX(collection_mode = True)
    myopf = opf.ContentOPF(outdirect, collection_mode = True)
    for (doc, xml) in documents:
        DOI = doc.getDOI()
        utils.fetchPLoSImages(DOI, cache_dir, outdirect, settings.caching)
        content.OPSContent(xml, DOI, outdirect, doc.front, doc.back)
        mytoc.takeArticle(doc)
        myopf.takeArticle(doc)
        
    mytoc.write(outdirect)
    myopf.write()
    utils.epubZip(outdirect)
    
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be 
    #taken whenever modifying this code
    if settings.cleanup:
        shutil.rmtree(outdirect)
    
    
    
def main():
    '''Main Script'''
    
    parser = argparse.ArgumentParser(description = 'OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version', version='OpenAccess_EPUB {0}'.format(__version__))
    #parser.add_argument('-q', '--quiet', action = 'store_true', default = False)
    parser.add_argument('-i', '--input', action = 'store', 
                        help = 'Input may be a path to a local directory, a URL to a PLoS journal article, or a PLoS DOI string')
    parser.add_argument('-o', '--output', action = 'store', default = settings.default_output, 
                        help = 'Use to specify a desired output directory')
    parser.add_argument('-s', '--save-xml', action = 'store', default = settings.xml_location, 
                        help = 'Use to specify a directory for storing downloaded xml files')
    parser.add_argument('-l', '--log-to', action = 'store', default = settings.log_location, 
                        help = 'Use to specify a non-default log directory')
    parser.add_argument('-c', '--cache', action = 'store', default = settings.cache_location, 
                        help = 'Use to specify a non-default cache directory')
    parser.add_argument('-b', '--batch', action = 'store', default = False, 
                        help = 'Use to specify a batch directory; each article inside will be processed.')
    parser.add_argument('-C', '--collection', action = 'store', default = False, 
                        help = 'Use to create an ePub file containing multiple resources.')
    args = parser.parse_args()
    
    #Check for directory existence, create if not found
    #This will break if the path has no immediate parent directory, this could 
    #be fixed but I am not sure if it should
    if not os.path.isdir(args.log_to):
        os.mkdir(args.log_to)
    if not os.path.isdir(args.cache):
        initCache(args.cache)
    if not os.path.isdir(args.save_xml):
        os.mkdir(args.save_xml)
    if not os.path.isdir(args.output):
        os.mkdir(args.output)
    
    #Initiate logging settings
    logname = os.path.join(args.log_to, 'temp.log')
    logging.basicConfig(filename = logname, level = logging.DEBUG)
    logging.info('OpenAccess_EPUB Log v.{0}'.format(__version__))
    
    if args.batch:
        download = False
        files = os.listdir(args.batch)
        for file in files:
            if not os.path.splitext(file)[1] == '.xml':
                pass
            else:
                filename = os.path.join(args.batch, file)
                document, xml_local = localInput(filename)
                input_name = os.path.splitext(os.path.split(xml_local)[1])[0]
                output_name = os.path.join(args.output, input_name)
                if os.path.isdir(output_name):
                    dirExists(output_name, args.batch)
                makeEPUB(document, xml_local, args.cache, output_name, args.log_to)
    
    if args.collection:
        t = 'Collection-{0}'.format(datetime.datetime(1,1,1).now().isoformat())
        output_name = os.path.join(args.output, t)
        with open(args.collection, 'r') as collection:
            inputs = collection.readlines()
        documents = []
        for input in inputs:
            if 'http://www' in input:
                download = True
                document, xml_local = urlInput(input.rstrip('\n'), args.save_xml)
            elif input[:4] == 'doi:':
                download = True
                document, xml_local = doiInput(input.rstrip('\n'), args.save_xml)
            else:
                download = False
                document, xml_local = localInput(input.rstrip('\n'))
            documents += [(document, xml_local)]
        makeCollectionEPUB(documents, args.cache, output_name, args.log_to)
    
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
            document, xml_local = localInput(args.input)
    
    #For now PloS naming will be maintained
    #The name of the processing directory and the .epub should be a string like
    #journal.pcbi.1002211
    #or if already re-named, it will assume the xml name
    input_name = os.path.splitext(os.path.split(xml_local)[1])[0]
    output_name = os.path.join(args.output, input_name)
    
    if os.path.isdir(output_name):
        dirExists(output_name, args.batch)
    
    makeEPUB(document, xml_local, args.cache, output_name, args.log_to)
        
    if download and not settings.save_xml:
        os.remove(xml_local)
    
    newname = u'{0}.log'.format(input_name)
    newname =  os.path.join(args.log_to, newname)
    os.rename(logname, newname)
    
if __name__ == '__main__':
    main()