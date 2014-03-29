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

log = logging.getLogger('openaccess_epub.package')

spine_item = namedtuple('Spine_Item', 'idref, linear')


class Package(object):
    """
    The Package class
    """

    def __init__(self, collection=False):
        self.spine = []
        self.collection = collection
        self.article = None
        self.all_articles = []
        self.doi = ''
        self.all_dois = []
        self.article_doi = ''
        self.journal_doi = ''

    def process(self, article):
        if self.article is not None and not self.collection:
            log.warning('Could not process additional article. Package only \
handles one article unless collection mode is set.')
            return False

        self.article = article
        self.article_doi = self.article.doi.split('/')[1]
        #self.all_dois.append(self.article.doi)
        #if self.collection:
            #self.title += ' ' + self.article.doi
        #else:
            #self.title += ' ' + self.article.publisher.nav_title(article)
        #for author in self.article.publisher.nav_creators(article):
            #self.authors.add(author)

        #Analyze the article to add entries to the spine
        dash_doi = self.article_doi.replace('.', '-')

        #Entry for the main content document
        main_idref = 'main-{0}-xhtml'.format(dash_doi)
        self.spine.append(spine_item(main_idref, True))

        #Entry for the biblio content document
        biblio_idref = 'biblio-{0}-xhtml'.format(dash_doi)
        if self.article.back is not None:
            if self.article.back.findall('.//ref'):
                self.spine.append(spine_item(biblio_idref,
                                             True))

    def add_article_to_spine(self):
        """
        Adds items to the self.spine list with the addition of a new article.
        Later, make_spine_itemrefs will take these entries for the creation of
        XML for the spine of the OPF file.
        """
        dashed_article_doi = self.article_doi.replace('.', '-')
        #Add main, which should not be optional
        main_idref = 'main-{0}-xhtml'.format(dashed_article_doi)
        self.spine.append(spine_itemref(main_idref, 'yes'))
        #Create biblio idref
        biblio_idref = 'biblio-{0}-xhtml'.format(dashed_article_doi)
        #Add biblio idref if there is a bibliography
        if self.article.back is not None:
            if self.article.back.findall('.//ref'):
                self.spine.append(spine_itemref(biblio_idref, 'yes'))
        #Create tables idref
        tables_idref = 'tables-{0}-xhtml'.format(dashed_article_doi)
        #Add the tables if there should be a tables file
        tables = self.article.document.findall('.//table')
        if tables:
            self.spine.append(spine_itemref(tables_idref, 'no'))

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

        manifest = etree.SubElement(package, 'manifest')
        for item in self.file_manifest(os.path.join(location, 'EPUB')):
            if item.attrib['id'] == 'toc-ncx':
                item.attrib['id'] = 'ncx'  # Special id for toc.ncx
            manifest.append(item)

        with open(os.path.join(location, 'EPUB', 'package.opf'), 'wb') as output:
            output.write(etree.tostring(document, encoding='utf-8', pretty_print=True))

    def render_EPUB3(self, location):
        log.info('Rendering Package Document for EPUB3')
        document = self._init_package_doc(version='3.0')
        package = document.getroot()

        manifest = etree.SubElement(package, 'manifest')
        for item in self.file_manifest(os.path.join(location, 'EPUB')):
            if item.attrib['id'] == 'nav-xhtml':
                item.attrib['id'] = 'htmltoc'  # Special id for nav.xhtml
                item.attrib['properties'] = 'nav'
            if item.attrib['id'] == 'toc-ncx':
                item.attrib['id'] = 'ncx'  # Special id for toc.ncx
            manifest.append(item)

        with open(os.path.join(location, 'EPUB', 'package.opf'), 'wb') as output:
            output.write(etree.tostring(document, encoding='utf-8', pretty_print=True))
