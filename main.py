"""main script"""
import gofetch, metadata, bibliography, output, tocncx, parsebody
from utils import OUT_DIR
import os.path

dofetch = False
dooutput = False
dobiblio = False
dotoc = False

import xml.dom.minidom as minidom

ARTICLE = 'test_data/article.xml'
doc = minidom.parse(ARTICLE)

# The <article> may have 4 parts defined parts
front = doc.getElementsByTagName('front')[0]
body = doc.getElementsByTagName('body')[0]
back = doc.getElementsByTagName('back')[0]
responses = doc.getElementsByTagName('response')

#The FrontMatter object handles the material in the <front> of the article
#ArticleMeta and JournalMeta objects are instantiated and held as 
#attributes of FrontMatter
frontmatter = metadata.FrontMatter(front)
bodymatter = parsebody.BodyMatter(body, doc)

filename = os.path.join(OUT_DIR, output.getTitle_str(frontmatter))

output.generateFrontpage(frontmatter)

if dobiblio:
    biblio = bibliography.Biblio(doc)
    biblio.output()

if dooutput:
    output.generateHierarchy(filename)
    output.epubZip(filename)
    if dofetch:
        gofetch.getimages(frontmatter, filename)
    
if dotoc:
    tocncx.generateTOC(frontmatter)