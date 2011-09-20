#! /usr/bin/python

import argparse
import sys
import os.path
import xml.dom.minidom as minidom

import metadata, bibliography, output, tocncx, parsebody
from article import Article

def main():
    '''main script'''
    
    parser = argparse.ArgumentParser(description = 'OpenAccess_EPUB Parser')
    parser.add_argument('-q', '--quiet', action = 'store_true', default = False)
    parser.add_argument('-i', '--input', action = 'store', 
                        default = 'test_data/article.xml')
    parser.add_argument('-o', '--output', action = 'store', 
                        default = 'test_output/')
    
    args = parser.parse_args()
    
    document = Article(minidom.parse(args.input))
    
    if args.output:
        document.fetchImages()
        document.output_epub(args.output)
        output.epubZip(args.output, document.titlestring())
    
if __name__ == '__main__':
    main()