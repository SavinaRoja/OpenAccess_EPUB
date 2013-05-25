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
Dublin Core specification and the dublincore module.
"""

import openaccess.utils as utils
import openaccess.dublincore as dublincore
import logging
import os
import time
import uuid
import xml.dom.minidom
from openaccess_epub.utils import OrderedSet
from .publisher_metadata import *

log = logging.getLogger('OPF')

single_ccal_rights = '''This is an open-access article distributed under the\
terms of the Creative Commons Attribution License, which permits unrestricted\
use, distribution, and reproduction in any medium, provided the original\
author and source are credited.'''

collection_ccal_rights = '''This is a collection of open-access articles\
distributed under the terms of the Creative Commons Attribution License, which\
permits unrestricted use, distribution, and reproduction in any medium,\
provided the original work is properly cited.'''


class OPF(oject):
    """
    This class represents the OPF file, its generation with input and how it
    renders to output.
    
    The OPF file handles three distinct tasks: Dublin Core Metadata about the
    ePub file, a file manifest the ePub, and a read-order spine for the ePub.
    
    When the OPF class initiates, it contains no content, creating only the
    basic file framework. To pass input articles to the OPF class, whether for
    Single Input Mode or for Collection Mode, use the OPF.take_article method.
    
    The OPF Class relies on a concept of internal state. This state represents
    the class' focus on a single article at a time. This is of little
    importance in Single Input mode, but is critical to Collection Mode.
    
    """
    def __init__(self, write_location=os.getcwd(), collection_mode=False):
        """
        Initialization arguments:
            write_location - Where this instance will write to
            collection_mode - To use Collection Mode, set to True

        Collection Mode can be turned on or off after initialization using the
        use_collection_mode() and use_single_mode methods() respectively.
        """
        #Set internal variables to defaults
        self.reset_state()
        #Set Collection Mode by argument
        self.collection_mode = collection_mode
        #Set metadata and spine data structures to defaults
        self.reset_metadata()
        self.reset_spine()
        #Create the basic document
        self.init_opf_document()


    def init_opf_document(self):
        """
        This method creates the initial DOM document for the content.opf file
        """
        impl = xml.dom.minidom.getDOMImplementation()
        self.document = impl.createDocument(None, 'package', None)
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
        opf_sub_elements = ['metadata', 'manifest', 'spine', 'guide']
        for el in opf_sub_elements:
            self.package.appendChild(self.doc.createElement(el))
        self.metadata_node, self.manifest_node, self.spine_node, self.guide_node = self.package.childNodes
        self.spine.setAttribute('toc', 'ncx')


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
            self.reset_spine()
            self.reset_metadata()
        #Set state
        self.article = article
        self.all_articles.append(self.article)
        self.doi = article.get_doi()
        self.all_dois.append(self.doi)
        self.article_doi, self.journal_doi = self.doi.split('/')
        #Add spine elements for article
        self.add_article_to_spine()
        #Pull metadata from article for OPF Dublin Core metadata
        self.extract_article_metadata()


    def add_article_to_spine(self):
        """
        
        """
        pass


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
            #identifier is defined in publisher_metadata as a namedtuple
            self.identifier = identifier(uuid.uuid4(), 'UUID')
            #title is empty string or nonempty string
            self.title = self.get_article_title(article)
            #A collection article gets no dc:date elements
        else:  # Single Mode Specific
            #identifier is None or Identifier(value, scheme)
            self.identifier = self.get_article_identifier(article)
            #title is empty string or nonempty string
            self.title = self.get_article_title(article)
            #date is OrderedSet([Date(year, month, day, event)])
            for date in self.get_article_date(article):
                self.date.add(date)

        #These are no different between Single and Collection Modes
        #language is OrderedSet([strings])
        self.language.add(self.get_article_language(article))
        #creator is OrderedSet([Creator(name, role, file_as)])
        for creator in self.get_article_creator(article):
            self.creator.add(creator)
        #contributor is OrderedSet([Contributor(name, role, file_as)])
        for contributor in self.get_article_contributor(article):
            self.contributor.add(contributor)
        #publisher is OrderedSet([strings])
        self.publisher = self.get_article_publisher(article)
        #description is OrderedSet([strings])
        self.description.add(self.get_article_description(article))
        #subject is OrderedSet([strings])
        for subject in self.get_article_subject(article):
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

    def reset_metadata(self):
        """
        Resets the variables for the metadata to defaults, also used in
        __init__ to set them at the beginning.

        For those metadata elements that may contain more than one value, their
        data structure is suited by an ordered set. This preserves the order
        of inclusion while omitting duplication.
        """
        #These must have a value to be valid
        self.identifier = None  # 1: Scheme determined method or collection_mode
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
                    new = self.manifest_node.appendChild(self.doc.createElement('item'))
                    if path:
                        new.setAttribute('href', '/'.join([path, filename]))
                    else:
                        new.setAttribute('href', filename)
                    new.setAttribute('media-type', mimetypes[ext])
                    if filename == 'toc.ncx':
                        new.setAttribute('id', 'ncx')
                    elif ext == 'png':
                        trim = path[7:]
                        new.setAttribute('id', '{0}-{1}'.format(trim, filename.replace('.', '-')))
                    else:
                        new.setAttribute('id', filename.replace('.', '-'))
        os.chdir(current_dir)


    def make_spine_itemrefs(self):
        """
        
        """
        pass


    def make_metadata_elements(self):
        """
        
        """
        pass


    def write(self):
        """
        Writing the OPF file is immediately preceded by jobs that finalize
        the OPF document. This includes the creation of the final manifest,
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
            output.write(self.document.toprettyxml(encoding='utf-8'))


    def use_collection_mode(self):
        """Enables Collection Mode, sets self.collection_mode to True"""
        self.collection_mode = True


    def use_single_mode(self):
        """Disables Collection Mode, sets self.collection_mode to False"""
        self.collection_mode = False
