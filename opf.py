from main import __version__
import datetime
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
        self.package = self.opf.lastChild
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
        self.collection_mode = collection_mode
        #Here we create a custom collection unique identifier string
        #Consists of software name and version along with timestamp
        t = datetime.datetime(1,1,1)
        self.ccuid = 'OpenAccess_EPUBv{0}-{1}'.format(__version__, 
                                                      t.utcnow().__str__())
        
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
        #If there are tables, make tables xml file
        tables = article.body.getElementsByTagName('table')
        #If there are refs, make biblio xml file
        if article.back:
            refs = article.back.getElementsByTagName('ref')
        else:
            refs = None
        self.addToSpine(aid_dashed, tables, refs)
        
        if not self.collection_mode:
            #Utilize the methods in the dublincore module to translate metadata
            dublincore.generateDCMetadata(self.opf, self.metadata, 
                                          ameta, jmeta)
        else:
            #These terms are sensible to include from each article contained
            #dublincore module contains alreadyExists() to avoid repetitive
            #declarations of metadata
            dublincore.dc_creator(self.opf, self.metadata, ameta)
            dublincore.dc_contributor(self.opf, self.metadata, ameta)
            dublincore.dc_subject(self.opf, self.metadata, ameta)
            self.collectionMetadata(ameta)
            
    def collectionMetadata(self, ameta):
        '''Some of the Dublin Core metadata items are nonsensical in the case 
        of a Collection and they are ignored. Some are of interest, but are 
        non-trivial to provide, and may require manual editing by the user. 
        This method provides provisional support for certain dc:terms that are 
        sensible, and independent of article content.'''
        dublincore.dc_format(self.opf, self.metadata)
        dublincore.dc_language(self.opf, self.metadata)
        dublincore.dc_type(self.opf, self.metadata)
        dublincore.dc_publisher(self.opf, self.metadata)
        dublincore.dc_identifier(self.opf, self.metadata, ameta, col_str = self.ccuid)
        #I want to be fair here with regards to copyright statements. All PLoS 
        #articles are Creative Commons, which allows free use, modification, 
        #and reproduction, so long as sources are attributed. Attribution to 
        #each article is tricky for collections within the ePub 2.0 spec and 
        #deserves deeper discussion. At this stage, I feel the following 
        #approach for dc:rights is acceptable, it acknowledges the CCAL 
        #rights declared in the original articles, while not mandating that 
        #any custom modifications made by potential users do the same.
        #The CCAL terms for the original content should be respected.
        cp_text = '''This is a collection of open-access articles published by 
PLoS and distributed under the terms of the Creative Commons Attribution 
License, which permits unrestricted use, distribution, and reproduction in any 
medium, provided the original author and source are credited.'''
        dublincore.dc_rights(self.opf, self.metadata, ameta, copyright_text = cp_text)
        title = 'A Collection of open-access PLoS Journal articles'
        dublincore.dc_title(self.opf, self.metadata, ameta, title_text = title)
        
    def addToSpine(self, id_string, tables, refs):
        idref = '{0}-' + '{0}-xml'.format(id_string)
        syn_ref = self.spine.appendChild(self.opf.createElement('itemref'))
        main_ref = self.spine.appendChild(self.opf.createElement('itemref'))
        bib_ref = self.opf.createElement('itemref')
        tab_ref = self.opf.createElement('itemref')
        for r, i, l in [(syn_ref, 'synop', 'yes'), (main_ref, 'main', 'yes'), 
                        (bib_ref, 'biblio', 'yes'), (tab_ref, 'tables', 'no')]:
            r.setAttribute('linear', l)
            r.setAttribute('idref', idref.format(i))
        if refs:
            self.spine.appendChild(bib_ref)
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
                    new = self.manifest.appendChild(self.opf.createElement('item'))
                    new.setAttribute('href', os.path.join(path, filename))
                    new.setAttribute('media-type', mimetypes[ext])
                    if filename == 'toc.ncx':
                        new.setAttribute('id', 'ncx')
                    elif ext == 'png':
                        id = os.path.dirname(path)
                        id = id[7:]
                        new.setAttribute('id', '{0}-{1}'.format(id, filename.replace('.', '-')))
                    else:
                        new.setAttribute('id', filename.replace('.', '-'))
        os.chdir(current_dir)
    
    def write(self):
        self.makeManifest()
        filename = os.path.join(self.location, 'OPS', 'content.opf')
        with open(filename, 'w') as output:
            output.write(self.opf.toprettyxml(encoding = 'utf-8'))
