"""
The OPF file has three basic jobs: it presents metadata in the Dublin Core
format, it presents a manifest of all the files within the ePub, and it
provides a spine for a document-level read order. The latter two jobs shall
depend very little, if at all, on the particular publisher or article. The
Dublin Core metadata will require publisher-specific definitions of metadata
conversion.
"""

import dublincore as dc
import datetime
import os.path
import utils
import xml.dom.minidom


class OPF(object):
    """
    Represents the OPF document and the methods needed to produce it. Dublin
    Core metadata is referenced by this class per publisher.
    """

    def __init__(self, version, location, collection_mode=False):
        self.doi = ''
        self.dois = []
        self.collection_mode = collection_mode
        self.version = version
        self.location = location
        #Initiate the document
        self.initOpfDocument()
        #List of articles included
        self.articles = []

    def initOpfDocument(self):
        """
        This method creates the initial DOM document for the content.opf file
        """
        impl = xml.dom.minidom.getDOMImplementation()
        self.doc = impl.createDocument(None, 'package', None)
        #Grab the root <package> node
        self.package = self.doc.lastChild
        #Set attributes for this node, including namespace declarations
        self.package.setAttribute('version', '2.0')
        self.package.setAttribute('unique-identifier', 'PrimaryID')
        self.package.setAttribute('xmlns:opf', 'http://www.idpf.org/2007/opf')
        self.package.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
        self.package.setAttribute('xmlns', 'http://www.idpf.org/2007/opf')
        self.package.setAttribute('xmlns:oebpackage', 'http://openebook.org/namespaces/oeb-package/1.0/')
        #Create the sub elements for <package>
        opf_subelements = ['metadata', 'manifest', 'spine', 'guide']
        for el in opf_subelements:
            self.package.appendChild(self.doc.createElement(el))
        self.metadata, self.manifest, self.spine, self.guide = self.package.childNodes
        self.spine.setAttribute('toc', 'ncx')
        #Here we create a custom collection unique identifier string
        #Consists of software name and version along with timestamp
        t = datetime.datetime(1, 1, 1)
        self.ccuid = 'OpenAccess_EPUBv{0}-{1}'.format('__version__',
                                                      t.utcnow().__str__())

    def parseArticle(self, article):
        """
        Process the contents of an article to build the content.opf
        """
        self.doi = article.getDOI()
        self.dois.append(self.doi)
        self.article = article
        self.a_doi = self.doi.split('/')[1]
        self.a_doi_dashed = self.a_doi.replace('.', '-')
        self.articles.append(article)
        if not self.collection_mode:
            self.singleMetadata(article.metadata)
        else:
            self.collectionMetadata(article.metadata)
        self.addToSpine()

    def singleMetadata(self, ameta):
        """
        This method handles the metadata for single article ePubs. Should be
        overridden by publisher-specific classes.
        """
        pass

    def collectionMetadata(self, ameta):
        """
        This method handles the metadata for a collection. Should be overridden
        by publisher-specific classes.
        """
        pass

    def makeManifest(self):
        """
        The Manifest declares all of the documents within the ePub (except
        mimetype and META-INF/container.xml). It should be generated as a
        final step in the ePub process and after all articles have been parsed
        into <metadata> and <spine>.
        """
        mimetypes = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'xml':
                     'application/xhtml+xml', 'png': 'image/png', 'css':
                     'text/css', 'ncx': 'application/x-dtbncx+xml', 'gif':
                     'image/gif'}
        current_dir = os.getcwd()
        os.chdir(self.location)
        for path, _subname, filenames in os.walk('OPS'):
            path = path[4:]
            if filenames:
                for filename in filenames:
                    _name, ext = os.path.splitext(filename)
                    ext = ext[1:]
                    new = self.manifest.appendChild(self.doc.createElement('item'))
                    new.setAttribute('href', os.path.join(path, filename))
                    new.setAttribute('media-type', mimetypes[ext])
                    if filename == 'toc.ncx':
                        new.setAttribute('id', 'ncx')
                    elif ext == 'png':
                        eid = os.path.dirname(path)
                        eid = id[7:]
                        new.setAttribute('id', '{0}-{1}'.format(eid, filename.replace('.', '-')))
                    else:
                        new.setAttribute('id', filename.replace('.', '-'))
        os.chdir(current_dir)

    def addToSpine(self):
        idref = '{0}-' + '{0}-xml'.format(self.a_doi_dashed)
        syn_ref = self.spine.appendChild(self.doc.createElement('itemref'))
        main_ref = self.spine.appendChild(self.doc.createElement('itemref'))
        bib_ref = self.doc.createElement('itemref')
        tab_ref = self.doc.createElement('itemref')
        for r, i, l in [(syn_ref, 'synop', 'yes'), (main_ref, 'main', 'yes'),
                        (bib_ref, 'biblio', 'yes'), (tab_ref, 'tables', 'no')]:
            r.setAttribute('linear', l)
            r.setAttribute('idref', idref.format(i))
        try:
            b = self.article.root_tag.getElementsByTagName('back')[0]
        except IndexError:
            pass
        else:
            if b.getElementsByTagName('ref'):
                self.spine.appendChild(bib_ref)
        if self.article.root_tag.getElementsByTagName('table-wrap'):
            self.spine.appendChild(tab_ref)

    def write(self):
        self.makeManifest()
        filename = os.path.join(self.location, 'OPS', 'content.opf')
        with open(filename, 'w') as output:
            output.write(self.doc.toprettyxml(encoding='utf-8'))


class FrontiersOPF(OPF):
    """
    This is the OPF class intended for use with Frontiers articles.
    """

    def singleMetadata(self, ameta):
        """
        This method handles the metadata for single article Frontiers ePubs.
        """
        #Make the dc:identifier using the DOI of the article
        dc_identifier = dc.identifier(self.doi, self.doc, primary=True)
        dc_identifier.setAttribute('opf:scheme', 'DOI')
        self.metadata.appendChild(dc_identifier)
        #Make the dc:language, it defaults to english
        self.metadata.appendChild(dc.language(self.doc))
        #Make the dc:title using the article title
        title = utils.serializeText(ameta.title.article_title, [])
        self.metadata.appendChild(dc.title(title, self.doc))
        #Make the dc:rights using the metadata in permissions
        s = utils.serializeText(ameta.permissions.statement, [])
        l = utils.serializeText(ameta.permissions.license, [])
        self.metadata.appendChild(dc.rights(' '.join([s, l]), self.doc))

    def collectionMetadata(self, ameta):
        """
        This method handles the metadata for a Frontiers article in a
        collection.
        """
        pass


class PLoSOPF(OPF):
    """
    This is the OPF class intended for use with PLoS articles.
    """

    def singleMetadata(self, ameta):
        """
        This method handles the metadata for single article PLoS ePubs.
        """
        pass

    def collectionMetadata(self, ameta):
        """
        This method handles the metadata for a PLoS article in a collection.
        """
        pass
