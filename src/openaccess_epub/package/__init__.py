# -*- coding: utf-8 -*-

"""
openaccess_epub.package provides facilities for producing EPUB package
documents

The Package Document carries bibliographic and structural metadata about an EPUB
Publication, and is thus the primary source of information about how to process
and display it. It is a part of both the EPUB 2 and EPUB 3 specifications and is
the point of processing which tells reading systems which version of EPUB the
document represents.
"""

#This module will be superceding the previouse opf module. It will become more
#general and capable of producing package info for EPUB2, and EPUB3.

#Standard Library modules
from collections import namedtuple
import logging
import os

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__
from openaccess_epub.utils import OrderedSet

log = logging.getLogger('openaccess_epub.package')

spine_item = namedtuple('Spine_Item', 'idref, linear')


class Package(object):
    """
    The Package class
    """

    def __init__(self, collection=False):
        self.collection = collection
        self.spine_list = []

        self.article = None
        self.article_doi = None

        self.all_dois = []  # Used to create UID
        self.all_articles = []

        #Metadata elements
        self.contributors = OrderedSet()      # 0+ Editors/Reviewers
        self.coverage = OrderedSet()          # 0+ Not used yet
        #self.creator = OrderedSet()          # 0+ Authors
        self.dates = OrderedSet()             # 0+ Publication date (probably)
        self.descriptions = OrderedSet()      # 0+ Long descriptions (abstracts)
        self.format = 'application/epub+zip'  # 1  Always epub
        self.language = OrderedSet()          # 1+ All languages present in doc
        self.publishers = OrderedSet()        # 0+ All publishers of content
        self.relation = OrderedSet()          # 0+ Not used yet
        self.rights = ''                      # 1  License, details TBD
        self.source = OrderedSet()            # 0+ Not used yet
        self.subjects = OrderedSet()          # 0+ Subjects covered in doc
        self.title = ''                       # 1  Title of publication
        self.type = 'text'                    # 1  Always text

    def process(self, article):
        """
        Ingests an article and processes it for metadata and elements to provide
        proper references in the EPUB spine.

        This method may only be called once unless the Package was instantiated
        in collection mode using ``Package(collection=True)``. It places entries
        in an internal spine list for the Main Content Document, the
        Bibliographic Content Document (if there are ref elements in Back), and
        the Tables Content Document (if there are table elements). It then
        employs the publisher specific methods for extracting article metadata
        using the article's publisher attribute (an instance of a Publisher
        class).

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            An article to be included in the EPUB, to be processed for metadata
            and appropriate content document references.
        """
        if self.article is not None and not self.collection:
            log.warning('Could not process additional article. Package only \
handles one article unless collection mode is set.')
            return False

        self.article = article
        self.article_doi = self.article.doi.split('/')[1]

        #Analyze the article to add entries to the spine
        dash_doi = self.article_doi.replace('.', '-')

        #Entry for the main content document
        main_idref = 'main-{0}-xhtml'.format(dash_doi)
        self.spine_list.append(spine_item(main_idref, True))

        #Entry for the biblio content document
        biblio_idref = 'biblio-{0}-xhtml'.format(dash_doi)
        if self.article.back is not None:
            if self.article.back.findall('.//ref'):
                self.spine_list.append(spine_item(biblio_idref, True))

        #Entry for the tables content document
        tables_idref = 'tables-{0}-xhtml'.format(dash_doi)
        if self.article.document.findall('.//table'):
            self.spine_list.append(spine_item(tables_idref, False))

        self.acquire_metadata()

    def acquire_metadata(self):
        """
        Handles the acquisition of metadata for both collection mode and single
        mode, uses the metadata methods belonging to the article's publisher
        attribute.
        """
        publisher = self.article.publisher
        if self.collection:  # collection mode metadata gathering
            pass
        else:  # single mode metadata gathering
            pass

        self.contributor = OrderedSet()       # 0+ Editors/Reviewers
        self.creator = OrderedSet()           # 0+ Authors
        self.date = OrderedSet()              # 0+ Publication date (probably)
        self.description = OrderedSet()       # 0+ Long descriptions (abstracts)
        self.language = OrderedSet()          # 1+ All languages present in doc
        self.publisher = OrderedSet()         # 0+ All publishers of content
        self.rights = ''                      # 1  License, details TBD
        self.subject = OrderedSet()           # 0+ Subjects covered in doc
        self.title = ''                       # 1  Title of publication

        #Common metadata gathering
        self.language.add(publisher.package_language())  # languages
        for creator in publisher.package_creator():  # creators
            self.creator.add(creator)
        for contributor in publisher.package_contributor():  # contributors
            self.contributor.add(contributor)
        self.publisher.add(publisher.package_publisher())  # publisher names
        self.description.add(publisher.package_description())  # descriptions
        self.subject.add(publisher.package_subject())  # subjects

        #Should creator and contributor even be separated?

        #Recall that metadata were reset in single mode during take_article
        #self.set_publisher_metadata_methods()
        #if self.collection_mode:  #Collection Mode Specific
            #pass  # Nothing specific to Collection Mode only at this time
        #else:  # Single Mode Specific
            ##identifier is None or Identifier(value, scheme)
            #id = self.get_article_identifier(self.article)
            #if id:  # Only override default UUID if successful
                #self.identifier = id
            ##title is empty string or nonempty string
            #self.title = self.get_article_title(self.article)
            ##date is OrderedSet([Date(year, month, day, event)])
            #for date in self.get_article_date(self.article):
                #self.date.add(date)

    def file_manifest(self, location):
        """
        An iterator through the files in a location which yields item elements
        suitable for insertion into the package manifest.
        """
        #Maps file extensions to mimetypes
        mimetypes = {'.jpg': 'image/jpeg',
                     '.jpeg': 'image/jpeg',
                     '.xml': 'application/xhtml+xml',
                     '.png': 'image/png',
                     '.css': 'text/css',
                     '.ncx': 'application/x-dtbncx+xml',
                     '.gif': 'image/gif',
                     '.tif': 'image/tif',
                     '.pdf': 'application/pdf',
                     '.xhtml': 'application/xhtml+xml',
                     '.ttf': 'application/vnd.ms-opentype',
                     '.otf': 'application/vnd.ms-opentype'}

        current_dir = os.getcwd()
        os.chdir(location)
        for dirpath, _dirnames, filenames in os.walk('.'):
            dirpath = dirpath[2:]  # A means to avoid dirpath prefix of './'
            for fn in filenames:
                fn_ext = os.path.splitext(fn)[-1]
                item = etree.Element('item')
                #Here we set three attributes: href, media-type, and id
                if not dirpath:
                    item.attrib['href'] = fn
                else:
                    item.attrib['href'] = '/'.join([dirpath, fn])
                item.attrib['media-type'] = mimetypes[fn_ext]
                #Special handling for common image types
                if fn_ext in ['.jpg', '.png', '.tif', '.jpeg']:
                    #the following lines assume we are using the convention
                    #where the article doi is prefixed by 'images-'
                    item.attrib['id'] = '-'.join([dirpath[7:],
                                                  fn.replace('.', '-')])
                else:
                    item.attrib['id'] = fn.replace('.', '-')
                yield item
        os.chdir(current_dir)

    def _init_package_doc(self, version):
        root = etree.XML('''\
<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:dcterms="http://purl.org/dc/terms/" version="{0}"
   unique-identifier="pub-identifier">\
</package>'''.format(version))
        document = etree.ElementTree(root)
        return document

    def render_EPUB2(self, location):
        log.info('Rendering Package Document for EPUB2')
        document = self._init_package_doc(version='2.0')
        package = document.getroot()

        #Make the Metadata
        metadata = etree.SubElement(package, 'metadata')

        #Make the Manifest
        manifest = etree.SubElement(package, 'manifest')
        for item in self.file_manifest(os.path.join(location, 'EPUB')):
            if item.attrib['id'] == 'toc-ncx':
                item.attrib['id'] = 'ncx'  # Special id for toc.ncx
            manifest.append(item)

        #Make the Spine
        spine = etree.SubElement(package, 'spine')
        spine.attrib['toc'] = 'ncx'
        for item in self.spine_list:
            itemref = etree.SubElement(spine, 'itemref')
            itemref.attrib['idref'] = item.idref
            itemref.attrib['linear'] = 'yes' if item.linear else 'no'

        with open(os.path.join(location, 'EPUB', 'package.opf'), 'wb') as output:
            output.write(etree.tostring(document, encoding='utf-8', pretty_print=True))

    def render_EPUB3(self, location):
        log.info('Rendering Package Document for EPUB3')
        document = self._init_package_doc(version='3.0')
        package = document.getroot()

        #Make the Metadata
        metadata = etree.SubElement(package, 'metadata')

        #Make the Manifest
        manifest = etree.SubElement(package, 'manifest')
        for item in self.file_manifest(os.path.join(location, 'EPUB')):
            if item.attrib['id'] == 'nav-xhtml':
                item.attrib['id'] = 'htmltoc'  # Special id for nav.xhtml
                item.attrib['properties'] = 'nav'
            if item.attrib['id'] == 'toc-ncx':
                item.attrib['id'] = 'ncx'  # Special id for toc.ncx
            manifest.append(item)

        #Make the Spine
        spine = etree.SubElement(package, 'spine')
        spine.attrib['toc'] = 'ncx'
        self.spine_list = [spine_item('htmltoc', False)] + self.spine_list
        for item in self.spine_list:
            itemref = etree.SubElement(spine, 'itemref')
            itemref.attrib['idref'] = item.idref
            itemref.attrib['linear'] = 'yes' if item.linear else 'no'

        with open(os.path.join(location, 'EPUB', 'package.opf'), 'wb') as output:
            output.write(etree.tostring(document, encoding='utf-8', pretty_print=True))
