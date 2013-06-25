# -*- coding: utf-8 -*-
"""
This module provides the basic tools necessary to create the Open Packaging
Format, OPF, file for OpenAccess_EPUB.

The OPF file has three basic jobs: it presents metadata about the file in the
Dublin Core prescribed vocabulary, it contains a manifest of all the files
within the ePub, and it provides a spine for a document-level read order.
This spine provides the read order that e-readers MUST support, while the NCX
provides a much finer-grained Table of Contents that e-readers SHOULD support.

The latter two of these jobs are likely to vary little in their action from
publisher to publisher, but care should be taken with the metadata parsing
from the input to output, as the publisher convention may differ and some of
the translation decisions are subjective.

Refer to the version of JPTS you are using and the jpts module, as well as the
Dublin Core specification.
"""

import logging
import os
import time
import uuid
from lxml import etree
from openaccess_epub.utils import OrderedSet
from .publisher_metadata import *
from collections import namedtuple

spine_itemref = namedtuple('SpineItemref', 'idref, linear')

log = logging.getLogger('OPF')

single_ccal_rights = '''This is an open-access article distributed under the \
terms of the Creative Commons Attribution License, which permits unrestricted \
use, distribution, and reproduction in any medium, provided the original \
author and source are credited.'''

collection_ccal_rights = '''This is a collection of open-access articles \
distributed under the terms of the Creative Commons Attribution License, which \
permits unrestricted use, distribution, and reproduction in any medium, \
provided the original work is properly cited.'''


class OPF(object):
    """
    This class represents the OPF file, its generation with input,and its
    output rendering.

    The OPF file handles three distinct tasks: Dublin Core Metadata about the
    ePub file, a file manifest the ePub, and a read-order spine for the ePub.

    When the OPF class initiates, it contains no content, creating only the
    basic file framework. To pass input articles to the OPF class, whether for
    Single Input Mode or for Collection Mode, use the OPF.take_article method.

    The OPF Class relies on a concept of internal state. This state represents
    the class' focus on a single article at a time. This is of little
    importance in Single Input mode, but is critical to Collection Mode.
    """
    def __init__(self, location=os.getcwd(), collection_mode=False, title=''):
        """
        Initialization arguments:
            location - Where this ePub is based
            collection_mode - To use Collection Mode, set to True
            title - What the ePub will be titled*

        Collection Mode can be turned on or off after initialization using the
        use_collection_mode() and use_single_mode methods() respectively.

        *An ePub's title is determined by the value of the <dc:title> element in
        the content.opf file. In Single Mode, this title is determined
        automatically from the article it receives in take_article(). If one
        wishes to create a workflow for Single Mode that uses a different title
        then use the OPF class method set_title() after passing an article to
        take_article(). In Collection Mode, the title must be manually supplied
        in some form or the ePub will have an empty string for a title that
        ought to be corrected manually afterwards. Initializing the OPF
        instance with the title argument, or calling set_title() at any time
        before writing will give it a title.
        """
        #Set Collection Mode by argument
        self.collection_mode = collection_mode
        #Set internal variables to defaults
        self.reset_state()
        #Set location by argument
        self.location = location
        #Create the basic document
        self.init_opf_document()
        #Set the title if given
        self.title = title

    def init_opf_document(self):
        """
        This method creates the initial DOM document for the content.opf file
        """
        root = etree.XML('''<?xml version="1.0"?>
<!DOCTYPE ncx
  PUBLIC '-//NISO//DTD ncx 2005-1//EN'
  'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'>
<package version="2.0" unique-identifier="PrimaryID" \
xmlns:opf="http://www.idpf.org/2007/opf" \
xmlns:dc="http://purl.org/dc/elements/1.1/" \
xmlns="http://www.idpf.org/2007/opf" \
xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
</package>''')
        self.document = etree.ElementTree(root)
        self.package = self.document.getroot()
        #Create the sub elements for <package>
        self.metadata_element = etree.SubElement(self.package, 'metadata')
        self.manifest_element = etree.SubElement(self.package, 'manifest')
        self.spine_element = etree.SubElement(self.package, 'spine')
        self.guide_element = etree.SubElement(self.package, 'guide')
        #Add attribute to spine element
        self.spine_element.attrib['toc'] = 'ncx'

    def take_article(self, article):
        """
        Receives an instance of the Article class. This modifies the internal
        state of the OPF class to focus on the new article for the purposes of
        extracting metadata and content information.
        
        In Collection Mode, the addition of new articles to the OPF class
        results in cumulative (in order of receipt) content. In Single Input
        Mode, the addition of a new article will erase any information from the
        previous article.
        """
        #Reset some things if taking a new article, this prevents accumulation
        #in Single Input Mode.
        if not self.collection_mode:
            self.reset_state()
        #Set state
        self.article = article
        self.all_articles.append(self.article)
        self.doi = article.get_DOI()
        self.all_dois.append(self.doi)
        self.journal_doi, self.article_doi = self.doi.split('/')
        #Add spine elements for article
        self.add_article_to_spine()
        #Pull metadata from article for OPF Dublin Core metadata
        self.extract_article_metadata()

    def extract_article_metadata(self):
        """
        This method calls set_publisher_metadata_methods to ensure that
        publisher-specific methods are being correctly employed. It then
        directs the acquisition of article metadata using these methods, while
        adjusting for collection_mode.
        """
        #Recall that metadata were reset in single mode during take_article
        self.set_publisher_metadata_methods()
        if self.collection_mode:  #Collection Mode Specific
            pass  # Nothing specific to Collection Mode only at this time
        else:  # Single Mode Specific
            #identifier is None or Identifier(value, scheme)
            id = self.get_article_identifier(self.article)
            if id:  # Only override default UUID if successful
                self.identifier = id
            #title is empty string or nonempty string
            self.title = self.get_article_title(self.article)
            #date is OrderedSet([Date(year, month, day, event)])
            for date in self.get_article_date(self.article):
                self.date.add(date)

        #These are no different between Single and Collection Modes
        #language is OrderedSet([strings])
        self.language.add(self.get_article_language(self.article))
        #creator is OrderedSet([Creator(name, role, file_as)])
        for creator in self.get_article_creator(self.article):
            self.creator.add(creator)
        #contributor is OrderedSet([Contributor(name, role, file_as)])
        for contributor in self.get_article_contributor(self.article):
            self.contributor.add(contributor)
        #publisher is OrderedSet([strings])
        self.publisher.add(self.get_article_publisher(self.article))
        #description is OrderedSet([strings])
        self.description.add(self.get_article_description(self.article))
        #subject is OrderedSet([strings])
        for subject in self.get_article_subject(self.article):
            self.subject.add(subject)

    def set_publisher_metadata_methods(self):
        """
        Sets internal methods to be publisher specific for the article at hand.
        """
        if self.journal_doi == '10.1371':
            self.get_article_identifier = plos_dc_identifier
            self.get_article_language = plos_dc_language
            self.get_article_title = plos_dc_title
            self.get_article_creator = plos_dc_creator
            self.get_article_contributor = plos_dc_contributor
            self.get_article_publisher = plos_dc_publisher
            self.get_article_description = plos_dc_description
            self.get_article_date = plos_dc_date
            self.get_article_subject = plos_dc_subject
        else:
            raise ValueError('This publisher, {0}, is not supported'.format(self.journal_doi))

    def reset_state(self):
        """
        Resets the internal state variables to defaults, also used in __init__
        to set them at the beginning.
        """
        self.article = None
        self.all_articles = []
        self.doi = ''
        self.all_dois = []
        self.article_doi = ''
        self.journal_doi = ''
        #Set metadata and spine data structures to defaults
        self.reset_metadata()
        self.reset_spine()

    def reset_metadata(self):
        """
        Resets the variables for the metadata to defaults, also used in
        __init__ to set them at the beginning.

        For those metadata elements that may contain more than one value, their
        data structure is suited by an ordered set. This preserves the order
        of inclusion while omitting duplication.
        """
        #These must have a value to be valid
        #identifier uses default fallback behavior of UUID
        self.identifier = self.identifier = identifier(str(uuid.uuid4()), 'UUID')
        self.language = OrderedSet()  # 1+: Defaults to "en"
        self.title = ''  # 1: A string for the Title
        #Rights is 1 only, I am at the moment assuming all OA is under CCAL
        if self.collection_mode:
            self.rights = collection_ccal_rights
        else:
            self.rights = single_ccal_rights
        #Authors should be namedtuples with .name, .role, and .file_as
        self.creator = OrderedSet()  # 0+: Authors
        #Editors should be namedtuples with .name, .role, and .file_as
        self.contributor = OrderedSet()  # 0+: Editors, reviewers
        self.publisher = OrderedSet()  # 0+: String for each publisher
        self.description = OrderedSet()  # 0+: Long description, often abstract text
        self.subject = OrderedSet()  # 0+: 
        self.date = OrderedSet()

        #These values are invariant, and will always be singular
        self.format = 'application/epub+zip'
        self.type = 'text'

        #These values are currently not employed
        self.coverage = OrderedSet()  # 0+?
        self.source = OrderedSet()  # 0+
        self.relation = OrderedSet()  # 0+

    def reset_spine(self):
        """
        Empties the list of all items added to the spine.
        """
        self.spine = []

    def make_file_manifest(self):
        """
        This function recursively traverses the ePub structure around the OPF
        file location to provide an index of all files. These files are then
        listed under the manifest node.
        """
        mimetypes = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'xml':
                     'application/xhtml+xml', 'png': 'image/png', 'css':
                     'text/css', 'ncx': 'application/x-dtbncx+xml', 'gif':
                     'image/gif', 'tif': 'image/tif', 'pdf': 'application/pdf'}
        #Acquiring the current directory allows us to return there when complete
        #Thus avoiding problems relating call location, while allowing paths
        #to be relative to the 
        current_dir = os.getcwd()
        os.chdir(self.location)
        for path, _subname, filenames in os.walk('OPS'):
            path = path[4:]  # Removes leading OPS or OPS/
            if filenames:
                for filename in filenames:
                    _name, ext = os.path.splitext(filename)
                    ext = ext[1:]
                    new = etree.SubElement(self.manifest_element, 'item')
                    if path:
                        new.attrib['href'] = '/'.join([path, filename])
                    else:
                        new.attrib['href'] = filename
                    new.attrib['media-type'] = mimetypes[ext]
                    if filename == 'toc.ncx':
                        new.attrib['id'] = 'ncx'
                    elif ext == 'png':
                        trim = path[7:]
                        new.attrib['id'] = '{0}-{1}'.format(trim, filename.replace('.', '-'))
                    else:
                        new.attrib['id'] = filename.replace('.', '-')
        os.chdir(current_dir)

    def add_article_to_spine(self):
        """
        Adds items to the self.spine list with the addition of a new article.
        Later, make_spine_itemrefs will take these entries for the creation of
        XML for the spine of the OPF file.
        """
        dashed_article_doi = self.article_doi.replace('.', '-')
        #Add main, which should not be optional
        main_idref = 'main-{0}-xml'.format(dashed_article_doi)
        self.spine.append(spine_itemref(main_idref, 'yes'))
        #Create biblio idref
        biblio_idref = 'biblio-{0}-xml'.format(dashed_article_doi)
        #Add biblio idref if there is a bibliography
        if self.article.back is not None:
            if self.article.back.findall('.//ref'):
                self.spine.append(spine_itemref(biblio_idref, 'yes'))
        #Create tables idref
        tables_idref = 'tables-{0}-xml'.format(dashed_article_doi)
        #Add the tables if there should be a tables file
        tables = self.article.document.findall('.//table')
        if tables:
            self.spine.append(spine_itemref(tables_idref, 'no'))

    def make_spine_itemrefs(self):
        """
        This is responsible for creating the itemref elements in the OPF spine.
        For every Article received, there should be a main document and
        usually, but not always, a biblio document. Some articles will have an
        html-tables document, that should receive an itemref, but it will not
        be placed in the linear order.
        """
        for itemref in self.spine:
            itemref_element = etree.SubElement(self.spine_element, 'itemref')
            itemref_element.attrib['idref'] = itemref.idref
            itemref_element.attrib['linear'] = itemref.linear

    def make_metadata_elements(self):
        """
        This generates Dublin Core metadata from the metadata structures that
        have been extracted from the article(s).

        Relevant specifications about Dublin Core are:
        http://dublincore.org/documents/2004/12/20/dces/
        http://idpf.org/epub/20/spec/OPF_2.0.1_draft.htm

        Only unicode text may go exist under the <dc:element> nodes.
        """
        #Create and add the dc:identifier element
        self.spawn_element(self.metadata_element, 'dc:identifier',
                           attrs={'opf:scheme': self.identifier.scheme,
                                  'id': 'PrimaryID'},
                           text=self.identifier.value)
        #Create and add the dc:language elements
        for lang in self.language:
            self.spawn_element(self.metadata_element, 'dc:language', text=lang)
        #Create and add the dc:title element
        self.spawn_element(self.metadata_element, 'dc:title', text=self.title)
        #Create and add the dc:rights element
        self.spawn_element(self.metadata_element, 'dc:rights',
                           text=self.rights)
        #Create and add the dc:creator elements
        for creator in self.creator:
            self.spawn_element(self.metadata_element, 'dc:creator',
                               attrs={'opf:role': creator.role,
                                      'opf:file-as': creator.file_as},
                               text=creator.name)
        #Create and add the dc:creator elements
        for contributor in self.contributor:
            self.spawn_element(self.metadata_element, 'dc:contributor',
                               attrs={'opf:role': contributor.role,
                                      'opf:file-as': contributor.file_as},
                               text=contributor.name)
        #Create and add the dc:date elements
        for date in self.date:
            month, day = int(date.month), int(date.day)
            date_text = date.year
            if month:
                date_text += '-{0}'.format(month)
                if day:
                    date_text += '-{0}'.format(day)
            self.spawn_element(self.metadata_element, 'dc:date',
                               attrs={'opf:event': date.event},
                               text=date_text)
        #Create and add the dc:publisher elements
        for publisher in self.publisher:
            self.spawn_element(self.metadata_element, 'dc:publisher',
                               text=publisher)
        #Create and add the dc:format element
        self.spawn_element(self.metadata_element, 'dc:format',
                           text=self.format)
        #Create and add the dc:type element
        self.spawn_element(self.metadata_element, 'dc:type', text=self.type)
        #Create and add the dc:description elements
        for description in self.description:
            self.spawn_element(self.metadata_element, 'dc:description',
                               text=description)
        #These are not really implemented yet, but they could be...
        #Create and add the dc:coverage, dc:source, and dc:relation elements
        for coverage in self.coverage:
            self.spawn_element(self.metadata_element, 'dc:coverage',
                               text=coverage)
        for source in self.source:
            self.spawn_element(self.metadata_element, 'dc:source', text=source)
        for relation in self.relation:
            self.spawn_element(self.metadata_element, 'dc:relation',
                               text=relation)

    def spawn_element(self, parent, tag_name, attrs=None, text=None):
        """
        A convenience function that works like etree.SubElement, except it will
        also add attributes by key-value pairs (attrs) and will set the
        new element's text to that passed by text argument.

        It will also do namespace correction for lxml
        """
        def ns_check(instring):
            if ':' not in instring:
                return instring
            else:
                prefix, suffix = instring.split(':')
                return '{'+self.package.nsmap[prefix]+'}'+suffix
        
        if attrs is None:
            attrs = {}
        new_element = etree.SubElement(parent, ns_check(tag_name))
        for attr_key in attrs.keys():
            new_element.attrib[ns_check(attr_key)] = attrs[attr_key]
        if text is not None:
            new_element.text = text

    def write(self):
        """
        Writing the OPF file is immediately preceded by jobs that finalize
        the OPF document. This includes the creation of the file manifest,
        the creation of the spine's itemrefs, and the creation of the Dublin
        Core metadata.

        Writing the OPF file should be one of the last jobs in the process of
        creating an ePUb, as modifications to the ePub not registered in the
        OPF file might invalidate/break the ePub.
        """
        self.make_file_manifest()
        self.make_spine_itemrefs()
        self.make_metadata_elements()
        filename = os.path.join(self.location, 'OPS', 'content.opf')
        with open(filename, 'wb') as output:
            output.write(etree.tostring(self.document, encoding='utf-8'))

    def use_collection_mode(self):
        """Enables Collection Mode, sets self.collection_mode to True"""
        self.collection_mode = True

    def use_single_mode(self):
        """Disables Collection Mode, sets self.collection_mode to False"""
        self.collection_mode = False

    def set_title(self, title):
        self.title = title
