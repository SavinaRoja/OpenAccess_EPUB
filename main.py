#! /usr/bin/python


__version__ = 'indev'

#Standard Library Modules
import argparse
import sys
import os.path
import urllib2
import urlparse

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
                        help = 'Use this flag to automatically delete the output directory upon completion')
    
    args = parser.parse_args()
    
    if 'http://www' in args.input:
        try:
            download = True
            address = urlparse.urlparse(args.input)
            _fetch = '/article/fetchObjectAttachment.action?uri='
            _id = address.path.split('/')[2]
            _rep = '&representation=XML'
            access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc, 
                                        _fetch, _id, _rep)
            open_xml = urllib2.urlopen(access)
            filename = open_xml.headers['Content-Disposition'].split('\"')[1]
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
            
            document = Article(filename)
            
        except:
            print('Invalid Link: Enter a corrected link or use local file')
            sys.exit()
    
    elif args.input[:4] == 'doi:':
        try:
            download = True
            doi_url = 'http://dx.doi.org/' + args.input[4:]
            page = urllib2.urlopen(doi_url)
            address = urlparse.urlparse(page.geturl())
            _fetch = '/article/fetchObjectAttachment.action?uri='
            _id = address.path.split('/')[2]
            _rep = '&representation=XML'
            access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc, 
                                        _fetch, _id, _rep)
            open_xml = urllib2.urlopen(access)
            filename = open_xml.headers['Content-Disposition'].split('\"')[1]
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
            
            document = Article(filename)
        except:
            print('Invalid DOI Link: Make sure that the address and format are correct')
            print('A valid entry looks like: \"doi:10.1371/journal.pcbi.1002222\"')
            sys.exit()
    else:
        download = False
        filename = args.input
        document = Article(filename)
    
    if args.output:
        outdirect = args.output
    else:
        outdirect = document.titlestring()
        
        output.generateHierarchy(outdirect)
        document.fetchImages(dirname = outdirect)
        content.OPSContent(filename, outdirect, document.front, 
                           document.back)
        tocncx.generateTOC(document.front, document.features, outdirect)
        output.generateOPF(document, outdirect)
        output.epubZip(outdirect, document.titlestring())
        
    if download and not args.save_xml:
        os.remove(filename)
    if args.cleanup:
        for root, dirs, files in os.walk(outdirect, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(outdirect)
        
    
if __name__ == '__main__':
    main()