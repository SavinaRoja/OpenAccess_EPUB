import os, os.path, zipfile, utils

def getTitle_str(fm):
    '''Creates a string for the title of the file and ebook'''
    titlestring = u'{0}_{1}{2}'.format(fm.journal_meta.identifier['pmc'],
                                       fm.article_meta.art_auths[0].surname,
                                       fm.article_meta.art_dates['collection'][2])
    return titlestring
    
def generateHierarchy(dirname):
    os.mkdir(dirname)
    os.mkdir(os.path.join(dirname, 'META-INF'))
    ops = os.path.join(dirname, 'OPS')
    os.mkdir(ops)
    css = os.path.join(ops, 'css')
    os.mkdir(css)
    images = os.path.join(ops, 'images')
    os.mkdir(images)
    figures = os.path.join(images, 'figures')
    os.mkdir(figures)
    tables = os.path.join(images, 'tables')
    os.mkdir(tables)
    supp = os.path.join(images, 'supplementary')
    os.mkdir(supp)
    eqn = os.path.join(images, 'equations')
    os.mkdir(eqn)
    
    # Create mimetype file in root directory
    mimepath = os.path.join(dirname, 'mimetype')
    mimetype = open(mimepath, 'w')
    mimetype.write('application/epub+zip')
    mimetype.close()
    
    # Create the container.xml file in META-INF
    meta_path = os.path.join(dirname, 'META-INF', 'container.xml')
    container = open(meta_path, 'w')
    container.write('''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OPS/{0}.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>'''.format(dirname))
    container.close()
    
def generateFrontpage(fm):
    
    doc, body = utils.initiateDocument('Frontpage')
    title = doc.createElement('title')
    title.appendChild(doc.createTextNode('Front'))
    
    abstract = fm.article_meta.abstract
    abstractheader = doc.createElement('h4')
    abstractheader.appendChild(doc.createTextNode('Abstract:'))
    abstract.insertBefore(abstractheader, abstract.firstChild)
    author_summary = fm.article_meta.author_summary
    summaryheader = doc.createElement('h4')
    summaryheader.appendChild(doc.createTextNode('Author Summary:'))
    author_summary.insertBefore(summaryheader, author_summary.firstChild)
    
    titleheader = doc.createElement('h2')
    titleheader.appendChild(doc.createTextNode(fm.article_meta.title))
    
    firstname = True
    for entry in fm.article_meta.art_auths:
        if firstname:
            authstr = entry.get_name()
            firstname = False
        else:
            authstr = authstr +', {0}'.format(entry.get_name())
    
    authors = doc.createElement('h3')
    authors.appendChild(doc.createTextNode(authstr))
    
    nodelist = [titleheader, authors, abstract, author_summary]
    
    for entry in nodelist:
        div = doc.createElement('div')
        div.appendChild(entry)
        body.appendChild(div)
        
    outdoc = open('{0}/frontpage.xml'.format(utils.OUT_DIR),'w')
    outdoc.write(doc.toprettyxml(encoding = 'UTF-8'))
    outdoc.close()
    
def epubZip(titlestring):
    """Zips up the output files into ePub package."""
    filename = '{0}.epub'.format(titlestring)
    epub = zipfile.ZipFile(filename, 'w')
    mimetype = os.path.join(titlestring, 'mimetype')
    epub.write(mimetype)
    epub.close()
    #os.system('mv {0}.epub ..'.format(titlestring))
