import os
import os.path
import utils
import dublincore
from xml.dom.minidom import getDOMImplementation

class contentOPF(object):
    '''A class to represent the OPF document.'''
    
    def __init__(self):
        pass

def generateOPF(article, dirname):
    '''Creates the content.opf document from an Article instance issued as 
    input'''
    
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
    
    #Get string from dirname sans "journal."
    jid = dirname.split('journal.')[1] #journal id string
    jid_dashed = jid.replace('.', '-')
    #File IDs
    syn_id = 'synop-{0}-xml'.format(jid_dashed)
    main_id = 'main-{0}-xml'.format(jid_dashed)
    bib_id = 'biblio-{0}-xml'.format(jid_dashed)
    tab_id = 'tables-{0}-xml'.format(jid_dashed)
    
    
    #Create useful accession points to article data
    artmeta = article.front.article_meta
    jrnmeta = article.front.journal_meta
    
    #Use the dublincore module to initialize the dc metadata
    dublincore.generateDCMetadata(mydoc, metadata, artmeta, jrnmeta)
    
    #manifest
    
    mimetypes = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'xml': 
                 'application/xhtml+xml', 'png': 'image/png', 'css':
                 'text/css', 'ncx': 'application/x-dtbncx+xml'}
    current_dir = os.getcwd()
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
                    newitem.setAttribute('id', filename.replace('.', '-'))
                    newitem.setAttribute('href', os.path.join(path, filename))
                    newitem.setAttribute('media-type', mimetypes[ext])
    
    tables = article.body.getElementsByTagName('table')
    
    os.chdir(current_dir)
    
    # Spine
    spine.setAttribute('toc', 'ncx')
    itemref_synop = mydoc.createElement('itemref')
    itemref_synop.setAttribute('idref', syn_id)
    itemref_synop.setAttribute('linear', 'yes')
    itemref_main = mydoc.createElement('itemref')
    itemref_main.setAttribute('idref', main_id)
    itemref_main.setAttribute('linear', 'yes')
    itemref_biblio = mydoc.createElement('itemref')
    itemref_biblio.setAttribute('idref', bib_id)
    itemref_biblio.setAttribute('linear', 'yes')
    itemref_tables = mydoc.createElement('itemref')
    itemref_tables.setAttribute('idref', tab_id)
    itemref_tables.setAttribute('linear', 'no')
    spine.appendChild(itemref_synop)
    spine.appendChild(itemref_main)
    spine.appendChild(itemref_biblio)
    if tables:
        spine.appendChild(itemref_tables)
    
    contentpath = os.path.join(dirname,'OPS','content.opf')
    with open(contentpath, 'w') as output:
        output.write(mydoc.toprettyxml(encoding = 'UTF-8'))
