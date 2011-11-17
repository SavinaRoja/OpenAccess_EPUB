#! /usr/bin/python

__version__ = '0.0.6b'

#Standard Library Modules
import argparse
import sys
import os.path
import shutil
import urllib2
import urlparse
import logging

#OpenAccess_EPUB Modules
import metadata
import output 
import tocncx 
import content
from settings import Settings
from article import Article

def initCache(cache_loc):
    os.mkdir(cache_loc)
    os.mkdir(os.path.join(cache_loc, 'model'))
    os.mkdir(os.path.join(cache_loc, 'PLoS'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'figures'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'tables'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'equations'))
    os.mkdir(os.path.join(cache_loc, 'model', 'images', 'supplementary'))

def main():
    '''main script'''
    settings = Settings()
    
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
    args = parser.parse_args()
    
    #Check for directory existence, create if not found
    #This will break if the path has no immediate parent directory, this could 
    #Be fixed but I am not sure if it should
    if not os.path.isdir(args.log_to):
        os.mkdir(args.log_to)
    
    if not os.path.isdir(args.cache):
        initCache(args.cache)
    
    if not os.path.isdir(args.save_xml):
        os.mkdir(args.save_xml)
    
    if not os.path.isdir(args.output):
        os.mkdir(args.output)
    
    logname = os.path.join('logs', 'temp.log')
    logging.basicConfig(filename = logname, level = logging.DEBUG)
    logging.info('OpenAccess_EPUB Log v.{0}'.format(__version__))
    
    if 'http://www' in args.input:
        download = True
        try:
            address = urlparse.urlparse(args.input)
            _fetch = '/article/fetchObjectAttachment.action?uri='
            _id = address.path.split('/')[2]
            _rep = '&representation=XML'
            access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc, 
                                        _fetch, _id, _rep)
            open_xml = urllib2.urlopen(access)
        except:
            print('Invalid Link: Enter a corrected link or use local file')
            sys.exit()
        
        else:
            filename = open_xml.headers['Content-Disposition'].split('\"')[1]
            if not os.path.isdir('downloaded_xml_files'):
                os.mkdir('downloaded_xml_files')
            filename = os.path.join('downloaded_xml_files', filename)
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
            
            document = Article(filename)
    
    elif args.input[:4] == 'doi:':
        download = True
        try:
            doi_url = 'http://dx.doi.org/' + args.input[4:]
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
            sys.exit()
            
        
        else:
            filename = open_xml.headers['Content-Disposition'].split('\"')[1]
            if not os.path.isdir('downloaded_xml_files'):
                os.mkdir('downloaded_xml_files')
            filename = os.path.join('downloaded_xml_files', filename)
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
            
            document = Article(filename)
        
    else:
        download = False
        filename = args.input
        document = Article(filename)
    
    outdirect = os.path.join(args.output, document.titlestring())
    if os.path.isdir(outdirect):
        print(u'The directory {0} already exists.'.format(outdirect))
        r = raw_input('Replace? [y/n]')
        if r in ['y', 'Y', '']:
            shutil.rmtree(outdirect)
        else:
            print('Aborting process.')
            sys.exit()
        
    
    print(u'Processing output to {0}.epub'.format(outdirect))
    output.generateHierarchy(outdirect)
    document.fetchImages(cache = args.cache, dirname = outdirect)
    content.OPSContent(filename, outdirect, document.front, 
                       document.back)
    tocncx.generateTOC(document.front, document.features, outdirect)
    output.generateOPF(document, outdirect)
    output.epubZip(outdirect)
        
    if download and not args.save_xml:
        os.remove(filename)
    
    newname = u'{0}.log'.format(document.titlestring())
    newname =  os.path.join(args.log_to, newname)
    os.rename(logname, newname)
    
    #WARNING: shutil.rmtree() is a recursive deletion function, care should be 
    #taken whenever modifying this code
    if settings.cleanup:
        shutil.rmtree(outdirect)
        
if __name__ == '__main__':
    main()