import os, os.path, zipfile, utils, dublincore

def generateHierarchy(dirname):
    os.mkdir(dirname)
    os.mkdir(os.path.join(dirname, 'META-INF'))
    ops = os.path.join(dirname, 'OPS')
    os.mkdir(ops)
    css = os.path.join(ops, 'css')
    os.mkdir(css)
    #Import CSS from resources/
    with open(os.path.join(css, 'article.css'), 'wb') as dest:
        with open('./resources/text.css', 'rb') as src:
            dest.write(src.read())
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

def generateOPF(article, dirname):
    '''Creates the content.opf document from an Article instance issued as 
    input'''
    from xml.dom.minidom import getDOMImplementation
    
    #Initiate a DOMImplementation for the OPF
    impl = getDOMImplementation()
    mydoc = impl.createDocument(None, 'package', None)
    
    package = mydoc.lastChild #grab the root package node
    package.setAttribute('version', '2.0')
    
    #Set attributes for this node, including namespace declarations
    package.setAttribute('unique-identifier', 'PrimaryID')
    package.setAttribute('xmlns:opf', 'http://www.idpf.org/2007/opf')
    package.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    package.setAttribute('xmlns', 'http://www.idpf.org/2007/opf')
    package.setAttribute('xmlns:oebpackage', 'http://openebook.org/namespaces/oeb-package/1.0/')
    
    #Create the metadata, manifest, spine, and guide nodes
    nodes = ['metadata', 'manifest', 'spine', 'guide']
    for node in nodes:
        package.appendChild(mydoc.createElement(node))
    metadata, manifest, spine, guide = package.childNodes
    
    #Create useful accession points to article data
    artmeta = article.front.article_meta
    jrnmeta = article.front.journal_meta
    
    #Use the dublincore module to initialize the dc metadata
    dublincore.generateDCMetadata(mydoc, metadata, artmeta, jrnmeta)
    
    #manifest
    
    mimetypes = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'xml': 
                 'application/xhtml+xml', 'png': 'image/png', 'css':
                 'text/css', 'ncx': 'application/x-dtbncx+xml'}
    os.chdir(dirname)
    for path, subname, filenames in os.walk('OPS'):
        path = path[4:]
        if filenames:
            for filename in filenames:
                if filename == 'toc.ncx':
                    newitem = manifest.appendChild(mydoc.createElement('item'))
                    newitem.setAttribute('id', 'ncx')
                    newitem.setAttribute('href', os.path.join(path, filename))
                    newitem.setAttribute('media-type', mimetypes['ncx'])
                else:
                    name, ext = os.path.splitext(filename)
                    ext = ext[1:]
                    newitem = manifest.appendChild(mydoc.createElement('item'))
                    newitem.setAttribute('id', '{0}-{1}'.format(name, ext))
                    newitem.setAttribute('href', os.path.join(path, filename))
                    newitem.setAttribute('media-type', mimetypes[ext])
                
    os.chdir('..')
    
    # Spine
    spine.setAttribute('toc', 'ncx')
    
    #<item id="ncx"
    #  href="myantonia.ncx"
    #  media-type="application/x-dtbncx+xml"/>
    
    contentpath = os.path.join(dirname,'OPS','content.opf')
    with open(contentpath, 'w') as output:
        output.write(mydoc.toxml(encoding = 'UTF-8'))
    
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
