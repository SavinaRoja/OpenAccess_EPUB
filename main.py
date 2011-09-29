#! /usr/bin/python

TESTARTICLE = 'test_data/journal.pone.0024702.xml'
# 'test_data/article.xml'
# 'test_data/journal.pone.0024702.xml'
# 'test_data/journal.pone.0025355.xml'
# 'test_data/journal.pcbi.1002126.xml'

import argparse
import sys
import os.path

import metadata, bibliography, output, tocncx, content
from article import Article

def main():
    '''main script'''
    
    parser = argparse.ArgumentParser(description = 'OpenAccess_EPUB Parser')
    parser.add_argument('-q', '--quiet', action = 'store_true', default = False)
    parser.add_argument('-i', '--input', action = 'store', 
                        default = TESTARTICLE)
    parser.add_argument('-o', '--output', action = 'store', 
                        default = 'test_output/')
    
    args = parser.parse_args()
    
    document = Article(args.input)
    
    if args.output:
        output.generateHierarchy(args.output)
        document.fetchImages(dirname = args.output)
        content.OPSContent(args.input, args.output, document.front, 
                           document.back)
        tocncx.generateTOC(document.front, document.features)
        output.generateOPF(document, args.output)
        output.epubZip(args.output, document.titlestring())
    
if __name__ == '__main__':
    main()