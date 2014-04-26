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
import datetime

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
#from openaccess_epub._version import __version__
from openaccess_epub.utils import OrderedSet

log = logging.getLogger('openaccess_epub.package')

spine_item = namedtuple('Spine_Item', 'idref, linear')


class Package(object):
    """
    The Package class
    """

    def __init__(self, collection=False, title=''):
        self.collection = collection
        self.spine_list = []

        self.article = None
        self.article_doi = None

        self.all_dois = []  # Used to create unique id and rights in collections
        #self.all_articles = []

        #Metadata elements
        self.pub_id = None
        self.contributors = OrderedSet()      # 0+ Authors/Editors/Reviewers
        self.coverage = OrderedSet()          # 0+ Not used yet
        self.dates = OrderedSet()             # 0+ Publication date (probably)
        self.descriptions = OrderedSet()      # 0+ Long descriptions (abstracts)
        self.format = 'application/epub+zip'  # 1  Always epub
        self.languages = OrderedSet()         # 1+ All languages present in doc
        self.publishers = OrderedSet()        # 0+ All publishers of content
        self.relation = OrderedSet()          # 0+ Not used yet
        self.rights = OrderedSet()            # 1  License, details TBD
        self.rights_associations = {}         # Keeps track per-article
        self.source = OrderedSet()            # 0+ Not used yet
        self.subjects = OrderedSet()          # 0+ Subjects covered in doc
        self.title = None                     # 1  Title of publication
        self.type = 'text'                    # 1  Always text

        if self.collection:  # Collections receive assigned titles
            self.title = title

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

        if article.publisher is None:
            log.error('''Package cannot be generated for an Article \
without a publisher!''')
            return
        self.article = article
        self.article_doi = self.article.doi.split('/')[1]
        self.all_dois.append(self.article.doi)

        #Analyze the article to add entries to the spine
        dash_doi = self.article_doi.replace('.', '-')

        #Entry for the main content document
        main_idref = 'main-{0}-xhtml'.format(dash_doi)
        self.spine_list.append(spine_item(main_idref, True))

        #Entry for the biblio content document
        biblio_idref = 'biblio-{0}-xhtml'.format(dash_doi)
        if self.article.root.xpath('./back/ref-list/ref'):
                self.spine_list.append(spine_item(biblio_idref, True))

        #Entry for the tables content document
        tables_idref = 'tables-{0}-xhtml'.format(dash_doi)
        if self.article.publisher.has_out_of_flow_tables():
            self.spine_list.append(spine_item(tables_idref, False))

        self.acquire_metadata()

    def acquire_metadata(self):
        """
        Handles the acquisition of metadata for both collection mode and single
        mode, uses the metadata methods belonging to the article's publisher
        attribute.
        """
        #For space economy
        publisher = self.article.publisher

        if self.collection:  # collection mode metadata gathering
            pass
        else:  # single mode metadata gathering
            self.pub_id = publisher.package_identifier()
            self.title = publisher.package_title()
            for date in publisher.package_date():
                self.dates.add(date)

        #Common metadata gathering
        for lang in publisher.package_language():
            self.languages.add(lang)  # languages
        for contributor in publisher.package_contributors():  # contributors
            self.contributors.add(contributor)
        self.publishers.add(publisher.package_publisher())  # publisher names
        desc = publisher.package_description()
        if desc is not None:
            self.descriptions.add(desc)
        for subj in publisher.package_subject():
            self.subjects.add(subj)  # subjects
        #Rights
        art_rights = publisher.package_rights()
        self.rights.add(art_rights)
        if art_rights not in self.rights_associations:
            self.rights_associations[art_rights] = [self.article.doi]
        else:
            self.rights_associations[art_rights].append(self.article.doi)

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

    def make_element(self, tagname, doc, attrs={}, text=''):
        new_element = etree.Element(self.ns_rectify(tagname, doc))
        for kwd, val in attrs.items():
            if val is None:  # None values will not become attributes
                continue
            new_element.attrib[self.ns_rectify(kwd, doc)] = val
        new_element.text = text
        return new_element

    def ns_rectify(self, tagname, document):
        if ':' not in tagname:
            return tagname
        else:
            ns, tag = tagname.split(':')
            return '{' + document.getroot().nsmap[ns] + '}' + tag

    def _init_package_doc(self, version):
        root = etree.XML('''\
<?xml version="1.0"?>
<package
   xmlns="http://www.idpf.org/2007/opf"
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:opf="http://www.idpf.org/2007/opf"
   xmlns:dcterms="http://purl.org/dc/terms/"
   version="{0}"
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

        #Metadata: Identifier
        if not self.collection:  # Identifier for single article
            ident = self.make_element('dc:identifier',
                                      document,
                                      {'id': 'pub-identifier',
                                       'opf:scheme': self.pub_id.scheme},
                                      self.pub_id.value)
            metadata.append(ident)
        else:  # Identifier for collection
            ident = self.make_element('dc:identifier',
                                      document,
                                      {'id': 'pub-identifier',
                                       'opf:scheme': 'DOI'},
                                      ','.join(self.all_dois))
            metadata.append(ident)

        #Metadata: Title
        #Divergence between single articles and collections for titles is
        #handled during initiation and selective metadata acquisition, not here
        title = self.make_element('dc:title', document, text=self.title)
        metadata.append(title)

        #Metadata: Languages
        for lang in self.languages:
            lang_el = self.make_element('dc:language', document, text=lang)
            metadata.append(lang_el)
        #So here's the deal about creators/contributors:
        #The EPUB2 OPF spec indicates a distinction between primary authors
        #(contained in dc:creator) and secondary authors (contained in
        #dc:contributor, along with all the other options in
        # http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#TOC2.2.6). As far
        #as I can think there is no real use case in academic articles for
        #<dc:contributor role="aut">... We'll just make all contributors with
        #the 'aut' role as <dc:creator>s
        for contrib in self.contributors:
            tag = 'dc:creator' if contrib.role == 'aut' else 'dc:contributor'
            metadata.append(self.make_element(tag,
                                              document,
                                              {'opf:role': contrib.role,
                                               'opf:file-as': contrib.file_as},
                                              contrib.name))

        #Metadata: Descriptions
        for description in self.descriptions:
            metadata.append(self.make_element('dc:description',
                                               document,
                                               text=description))

        #Metadata: Subjects
        for subject in self.subjects:
            metadata.append(self.make_element('dc:subject',
                                              document,
                                              text=subject))

        #Metadata: Format
        metadata.append(self.make_element('dc:format',
                                          document,
                                          text=self.format))

        #Metadata: Publishers
        for publisher in self.publishers:
            metadata.append(self.make_element('dc:publisher',
                                              document,
                                              text=publisher))

        #Metadata: Dates
        for date in self.dates:
            #I use str coercion just to be safe, in case someone returns ints
            date_text = str(date.year)
            if date.month:
                date_text = '-'.join([date_text, str(date.month)])
                if date.day:
                    date_text = '-'.join([date_text, str(date.day)])
            metadata.append(self.make_element('dc:date',
                                              document,
                                              {'opf:event': date.event},
                                              date_text))

        #Metadata: Rights
        if self.collection:
            if len(self.rights) == 1:  # Only one license string present
                rights_text = '''\
All articles in this collection published according to the following license:
'''
                rights_text = ''.join([rights_text, self.rights.pop()])
            else:  # More than one, we need to refer to rights_associations
                rights_text = '''\
Articles in this collection were published according to different licenses. Each
unique license will be listed below, preceded by every article DOI to which it
applies.'''
                for lic, doi_list in self.rights_associations.items():
                    doi_line = ','.join(doi_list)
                    rights_text = '\n'.join([rights_text, doi_line, lic])
                metadata.append(self.make_element('dc:rights',
                                                  document,
                                                  text=rights_text))

        else:
            metadata.append(self.make_element('dc:rights',
                                              document,
                                              text=self.rights.pop()))

        #Not Implemented Metadata: Source, Type, Coverage, Relation

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

        #Metadata: Identifier
        today = datetime.date.today().strftime('%Y.%m.%d')
        if not self.collection:  # Identifier for single article
            ident = self.make_element('dc:identifier',
                                      document,
                                      {'id': 'pub-identifier'},
                                      '.'.join([self.pub_id.value, today]))
            metadata.append(ident)
        else:  # Identifier for collection
            ident = self.make_element('dc:identifier',
                                      document,
                                      {'id': 'pub-identifier'},
                                      ','.join(self.all_dois) + '.' + today)
            metadata.append(ident)
        #Metadata: Identifier Refinement
        meta = self.make_element('meta',
                                 document,
                                 {'refines': '#pub-identifier',
                                  'property': 'identifier-type',
                                  'scheme': 'onix:codelist5'})
        if self.collection:  # Collections are always DOIs currently
            meta.text = '06'
            metadata.append(meta)
        else:
            if self.pub_id.scheme is not None:
                if self.pub_id.scheme == 'DOI':
                    meta.text = '06'
                    metadata.append(meta)
                else:  # We could do an ONIXlist lookup map here
                    raise ValueError('Unhandled id scheme!')

        #Metadata: Title
        #Divergence between single articles and collections for titles is
        #handled during initiation and selective metadata acquisition, not here
        title = self.make_element('dc:title',
                                  document,
                                  {'id': 'pub-title'},
                                  text=self.title)
        metadata.append(title)

        #Metadata: Title Refinement
        meta = self.make_element('meta',
                                 document,
                                 {'refines': '#pub-title',
                                  'property': 'title-type'},
                                 'main')
        metadata.append(meta)

        #Metadata: Languages
        for lang in self.languages:
            lang_el = self.make_element('dc:language', document, text=lang)
            metadata.append(lang_el)

        #Metadata: Contributors/Creators
        #So here's the deal about creators/contributors:
        #The EPUB2 OPF spec indicates a distinction between primary authors
        #(contained in dc:creator) and secondary authors (contained in
        #dc:contributor, along with all the other options in
        # http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#TOC2.2.6). As far
        #as I can think there is no real use case in academic articles for
        #<dc:contributor role="aut">... We'll just make all contributors with
        #the 'aut' role as <dc:creator>s
        contrib_count = 0
        for contrib in self.contributors:
            tag = 'dc:creator' if contrib.role == 'aut' else 'dc:contributor'
            contrib_id = 'contrib{0}'.format(contrib_count)
            metadata.append(self.make_element(tag,
                                              document,
                                              {'id': contrib_id},
                                              text=contrib.name))

            #Metadata: Contributors/Creators Refinement
            #MARC Relators: http://www.loc.gov/marc/relators/relaterm.html
            #MARC Relators: http://www.loc.gov/marc/relators/relacode.html
            role_meta = self.make_element('meta',
                                          document,
                                          {'refines': '#' + contrib_id,
                                           'property': 'role',
                                           'scheme': 'marc:relators'})
            if contrib.role is not None:
                role_meta.text = contrib.role
                metadata.append(role_meta)

            file_as_meta = self.make_element('meta',
                                             document,
                                             {'refines': '#' + contrib_id,
                                              'property': 'file-as'})

            if contrib.file_as is not None:
                file_as_meta.text = contrib.file_as
                metadata.append(file_as_meta)
            contrib_count += 1

        #Metadata: Descriptions
        for description in self.descriptions:
            metadata.append(self.make_element('dc:description',
                                               document,
                                               text=description))

        #Metadata: Subjects
        for subject in self.subjects:
            metadata.append(self.make_element('dc:subject',
                                              document,
                                              text=subject))

        #Metadata: Format
        metadata.append(self.make_element('dc:format',
                                          document,
                                          text=self.format))

        #Metadata: Publishers
        for publisher in self.publishers:
            metadata.append(self.make_element('dc:publisher',
                                              document,
                                              text=publisher))

        #Metadata: Dates
        #EPUB3 differs significantly from EPUB2, only one dc:date is allowed
        #and it must be the date of EPUB publication
        #Must also be of proper format: http://www.w3.org/TR/NOTE-datetime
        simple_date = datetime.date.today().strftime('%Y-%m-%d')
        metadata.append(self.make_element('dc:date',
                                          document,
                                          {'id': 'pub-date'},
                                          simple_date))
        #Must have meta with dcterms:modified
        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        metadata.append(self.make_element('meta',
                                          document,
                                          {'property': 'dcterms:modified'},
                                          now))
        #Metadata: Dates Refinement
        #values are dateAccepted, dateCopyrighted, dateSubmitted
        accepted = self.make_element('meta',
                                     document,
                                     {'refines': '#pub-date',
                                      'property': 'dcterms:dateAccepted'})
        copyrighted = self.make_element('meta',
                                        document,
                                        {'refines': '#pub-date',
                                         'property': 'dcterms:dateCopyrighted'})
        submitted = self.make_element('meta',
                                      document,
                                      {'refines': '#pub-date',
                                       'property': 'dcterms:dateSubmitted'})

        def date_text(date):
            text = str(date.year)
            if date.month:
                text = '-'.join([text, str(date.month)])
                if date.day:
                    text = '-'.join([text, str(date.day)])
            return text

        for date in self.dates:
            if date.event == 'accepted':
                accepted.text = date_text(date)
                metadata.append(accepted)
            elif date.event == 'copyrighted':
                copyrighted.text = date_text(date)
                metadata.append(copyrighted)
            elif date.event == 'submitted':
                submitted.text = date_text(date)
                metadata.append(submitted)

        #Metadata: Rights
        if self.collection:
            if len(self.rights) == 1:  # Only one license string present
                rights_text = '''\
All articles in this collection published according to the following license:
'''
                rights_text = ''.join([rights_text, self.rights.pop()])
            else:  # More than one, we need to refer to rights_associations
                rights_text = '''\
Articles in this collection were published according to different licenses. Each
unique license will be listed below, preceded by every article DOI to which it
applies.'''
                for lic, doi_list in self.rights_associations.items():
                    doi_line = ','.join(doi_list)
                    rights_text = '\n'.join([rights_text, doi_line, lic])
            metadata.append(self.make_element('dc:rights',
                                              document,
                                              text=rights_text))

        else:
            metadata.append(self.make_element('dc:rights',
                                              document,
                                              text=self.rights.pop()))

        #Not Implemented Metadata: Source, Type, Coverage, Relation

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
        for item in self.spine_list:
            itemref = etree.SubElement(spine, 'itemref')
            itemref.attrib['idref'] = item.idref
            itemref.attrib['linear'] = 'yes' if item.linear else 'no'

        with open(os.path.join(location, 'EPUB', 'package.opf'), 'wb') as output:
            output.write(etree.tostring(document, encoding='utf-8', pretty_print=True))
