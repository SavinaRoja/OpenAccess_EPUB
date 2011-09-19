import os, os.path, zipfile, utils

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
    with open(mimepath, 'w') as mimetype:
        mimetype.write('application/epub+zip')
    
    # Create the container.xml file in META-INF
    meta_path = os.path.join(dirname, 'META-INF', 'container.xml')
    with open(meta_path, 'w') as container_xml:
        container_xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>''')
    
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
    
def generateOPF(article, dirname):
    '''Creates the content.opf document from an Article instance issued as input'''
    from xml.dom.minidom import getDOMImplementation
    from utils import createDCElement
    
    #Initiate a DOMImplementation for the OPF
    impl = getDOMImplementation()
    mydoc = impl.createDocument(None, 'package', None)
    
    package = mydoc.lastChild #grab the root package node
    package.setAttribute('version', '2.0')
    
    #Set attributes for this node, including namespace declarations
    package.setAttribute('unique-identifier', 'PrimaryID')
    package.setAttribute('xmlns:opf', 'http://www.idpf.org/2007/opf')
    package.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    
    # Currently, the Dublin Core will only be extended by the OPF Spec
    # See http://old.idpf.org/2007/opf/OPF_2.0_final_spec.html#Section2.2
    
    #Create the metadata, manifest, spine, and guide nodes
    nodes = ['metadata', 'manifest', 'spine', 'guide']
    for node in nodes:
        package.appendChild(mydoc.createElement(node))
    metadata, manifest, spine, guide = package.childNodes
    
    #Create useful accession points to article data
    artmeta = article.front.article_meta
    jrnmeta = article.front.journal_meta
    
    metadata.appendChild(createDCElement(mydoc, 'dc:title', artmeta.title))
    metadata.appendChild(createDCElement(mydoc, 'dc:rights', artmeta.art_copyright_statement))
    
    for auth in artmeta.art_auths:
        metadata.appendChild(createDCElement(mydoc, 'dc:creator', auth.get_name(), 
                                             {'opf:role': 'aut', 'opf:file-as': auth.get_fileas_name()}))
    
    for contr in artmeta.art_edits:
        metadata.appendChild(createDCElement(mydoc, 'dc:contributor', 
                                             contr.get_name(), 
                                             {'opf:role': 'edt', 'opf:file-as': contr.get_fileas_name()}))
    
    contentpath = os.path.join(dirname,'OPS','content.opf')
    with open(contentpath, 'w') as output:
        output.write(mydoc.toprettyxml(encoding = 'UTF-8'))
    
def epubZip(inputdirectory, name):
    """Zips up the input file directory into an ePub file."""
    filename = '{0}.epub'.format(name)
    epub = zipfile.ZipFile(filename, 'w')
    os.chdir(inputdirectory)
    epub.write('mimetype')
    utils.recursive_zip(epub, 'META-INF')
    utils.recursive_zip(epub, 'OPS')
    epub.close()
    os.chdir('..')
