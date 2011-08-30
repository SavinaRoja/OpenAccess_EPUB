#! /usr/bin/python

import argparse
import sys
import os.path
import xml.dom.minidom as minidom

import gofetch, metadata, bibliography, output, tocncx, parsebody
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
        document.output_epub(args.output)
        document.fetchImages()
        output.epubZip(args.output, document.titlestring())
    
    # The <article> may have 4 parts defined
    #front = doc.getElementsByTagName('front')[0]
    #body = doc.getElementsByTagName('body')[0]
    #back = doc.getElementsByTagName('back')[0]
    #responses = doc.getElementsByTagName('response')
    
    #The FrontMatter object handles the material in the <front> of the article
    #ArticleMeta and JournalMeta objects are instantiated and held as 
    #attributes of FrontMatter
    #frontmatter = metadata.FrontMatter(front)
    #bodymatter = parsebody.BodyMatter(body, doc)
    
    #filename = os.path.join(OUT_DIR, output.getTitle_str(frontmatter))
    
    #output.generateFrontpage(frontmatter)
    
    #if dobiblio:
    #    biblio = bibliography.Biblio(doc)
    #    biblio.output()
    #
    #if dooutput:
    #    output.generateHierarchy(filename)
    #    output.epubZip(filename)
    #if dofetch:
    #    gofetch.getimages(frontmatter, filename)
    
    #if dotoc:
    #    tocncx.generateTOC(frontmatter)
        
if __name__ == '__main__':
    main()