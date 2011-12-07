import os
import os.path
import utils
import dublincore
from xml.dom.minidom import getDOMImplementation

class ContentOPF(object):
    '''A class to represent the OPF document.'''
    
    def __init__(self, location, collection_mode = False):
        #Create a DOMImplementation for the OPF
        impl = getDOMImplementation()
        self.opf = impl.createDocument(None, 'package', None)
        #Grab the root <package> node
        self.package = mydoc.lastChild
        #Set attributes for this node, including namespace declarations
        self.package.setAttribute('version', '2.0')
        self.package.setAttribute('unique-identifier', 'PrimaryID')
        self.package.setAttribute('xmlns:opf', 'http://www.idpf.org/2007/opf')
        self.package.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
        self.package.setAttribute('xmlns', 'http://www.idpf.org/2007/opf')
        self.package.setAttribute('xmlns:oebpackage', 'http://openebook.org/namespaces/oeb-package/1.0/')
        #Create the sub elements for <package>
        opf_subelements = ['metadata', 'manifest', 'spine', 'guide']
        for element in opf_subelements:
            self.package.appendChild(self.opf.createElement(element))
        self.metadata, self.manifest, self.spine, self.guide = self.package.childNodes
        self.spine.setAttribute('toc', 'ncx')
        #Due to importance in relative positioning of the content.opf file to 
        #other files in the the packaged, the contentOPF instance shoudl be 
        #aware of its location
        self.location = location
        #Make a list of articles, even if only one expected
        self.articles = []
        
    def takeArticle(self, article):
        '''Handles the input from an article. The OPF Package processes the 
        article for metadata and specific filename-ID associations. Other jobs 
        are independent of article material and are handled elsewhere.'''
        #Add the Article to the list
        self.articles += [article]
        #Easy accession of metadata
        ameta = article.front.article_meta
        jmeta = article.front.journal_meta
        #Create appropriate idrefs, these are mapped to packaged files in 
        #the manifest. Because this is simple and we have set expectations
        #<spine> can be appended immediately
        for (_data, _id) in ameta.identifiers:
            if _id == 'doi':
                aid = _data.split('journal.')[1]
        aid_dashed = aid.replace('.', '-')
        tables = article.body.getElementsByTagName('table')
        self.addToSpine(aid_dashed, tables)
        
        if not self.collection_mode:
            #Utilize the methods in the dublincore module to translate metadata
            dublincore.generateDCMetadata(self.opf, self.metadata, 
                                          self.ameta, self.jmeta)
        else:
            dublincore.dc_format(self.opf, self.metadata)
        
    def addToSpine(self, id_string, tables):
        idref = '{0}-' + '{0}-xml'.format(id_string)
        syn_ref = self.spine.appendChild(self.opf.createElement('itemref'))
        main_ref = self.spine.appendChild(self.opf.createElement('itemref'))
        bib_ref = self.spine.appendChild(self.opf.createElement('itemref'))
        tab_ref = self.opf.createElement('itemref')
        for r, i, l in [(syn_ref, 'synop', 'yes'), (main_ref, 'main', 'yes'), 
                        (bib_ref, 'biblio', 'yes'), (tab_ref, 'tables', 'no')]:
            r.setAttribute('linear', l)
            r.setAttribute(idref.format(i))
        if tables:
            self.spine.appendChild(tab_ref)
    
    def makeManifest(self):
        '''The Manifest declares all of the documents within the ePub (except 
        mimetype and META-INF/container.xml). It should be generated as a 
        final step in the ePub process and after all articles have been parsed 
        into <metadata> and <spine>.'''
        mimetypes = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'xml': 
                     'application/xhtml+xml', 'png': 'image/png', 'css':
                     'text/css', 'ncx': 'application/x-dtbncx+xml'}
        current_dir = os.getcwd()
        os.chdir(self.location)
        for path, subname, filenames in os.walk('OPS'):
            path = path[4:]
            if filenames:
                for filename in filenames:
                    name, ext = os.path.splitext(filename)
                    ext = ext[1:]
                    new = self.manifest.appendChild(mydoc.createElement('item'))
                    new.setAttribute('href', os.path.join(path, filename))
                    new.setAttribute('media-type', mimetypes[ext])
                    if filename == 'toc.ncx':
                        new.setAttribute('id', 'ncx')
                    else:
                        new.setAttribute('id', filename.replace('.', '-'))
        os.chdir(current_dir)
    
    def write(self):
        self.makeManifest()
        filename = os.path.join(self.location, 'OPS', 'content.opf')
        with open(filename, 'w') as output:
            output.write(self.toc.toprettyxml(encoding = 'utf-8'))

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
