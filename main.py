#! /usr/bin/python

__version__ = '0.0.4'

#Standard Library Modules
import argparse
import sys
import os.path
import urllib2
import urlparse
import logging

#OpenAccess_EPUB Modules
import metadata
import output 
import tocncx 
import content
from article import Article

def main():
    '''main script'''
    
    parser = argparse.ArgumentParser(description = 'OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version', version='OpenAccess_EPUB {0}'.format(__version__))
    #parser.add_argument('-q', '--quiet', action = 'store_true', default = False)
    parser.add_argument('-i', '--input', action = 'store', 
                        help = 'Input may be a path to a local directory, a URL to a PLoS journal article, or a PLoS DOI string')
    parser.add_argument('-o', '--output', action = 'store', 
                        help = 'Use to specify a desired output directory')
    parser.add_argument('-s', '--save-xml', action = 'store_true', default = False, 
                        help = 'If downloading the article xml file, use this flag to save it after completion')
    parser.add_argument('-c', '--cleanup', action = 'store_true', default = False, 
                        help = 'Use this flag to automatically delete the pre-package output directory upon completion')
    parser.add_argument('-l', '--logging', action = 'store_true', default = False, 
                        help = 'Turn on logging. Saves a logfile in the logs directory for the process.')
    args = parser.parse_args()
    
    if not os.path.isdir('logs'):
        os.mkdir('logs')
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
    
    if args.output:
        outdirect = os.path.join(args.output, document.titlestring())
        if not os.path.isdir(args.output):
            os.mkdir(args.output)
    else:
        outdirect = document.titlestring()
    
    print(u'Processing output to {0}.epub'.format(outdirect))
    output.generateHierarchy(outdirect)
    document.fetchImages(dirname = outdirect)
    content.OPSContent(filename, outdirect, document.front, 
                       document.back)
    tocncx.generateTOC(document.front, document.features, outdirect)
    output.generateOPF(document, outdirect)
    output.epubZip(outdirect)
        
    if download and not args.save_xml:
        os.remove(filename)
    
    if args.logging: #rename the log file, or it will be overwritten next time
        newname = u'{0}.log'.format(document.titlestring())
        newname =  os.path.join('logs', newname)
        os.rename(logname, newname)
    
    #WARNING: THIS IS A RECURSIVE DELETION FUNCTION
    #DO NOT CHANGE THIS OR THE CREATION OF OUTDIRECT WITHOUT EXTREME CAUTION
    #YOU MIGHT DELETE MORE THAN YOU WANT...
    if args.cleanup:
        for root, dirs, files in os.walk(outdirect, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(outdirect)
        
    
if __name__ == '__main__':
    main()