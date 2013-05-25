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
        if not self.collection_mode:
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
        self.identifier = None  # 1: Scheme determined by collection mode
        self.language = OrderedSet()  # 1+: Defaults to "en"
        self.title = ''  # 1: A string for the Title
        #Rights is 1 only, I am at the moment assuming all OA is under CCAL
        if self.collection_mode:
            self.rights = collection_ccal_rights
        else:
            self.rights = single_ccal_rights
        #Authors should be namedtuples with .name and .fileas
        self.creator = OrderedSet()  # 0+: Authors
        #Editors should be namedtuples with .name and .fileas
        self.contributor = OrderedSet()  # 0+: Editors
        self.publisher = OrderedSet()  # 0+: String for each publisher
        self.description = OrderedSet()  # 0,1,+?: Long description, often abstract text
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


    def make_file_manifest(self):
        """
        This function recursively traverses the ePub structure around the OPF
        file location to provide an index of all files. These files are then
        listed under the manifest node.
        """
        pass


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


    def use_collection_mode(self):
        """Enables Collection Mode, sets self.collection_mode to True"""
        self.collection_mode = True


    def use_single_mode(self):
        """Disables Collection Mode, sets self.collection_mode to False"""
        self.collection_mode = False


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
        with open(filename, 'wb') as output:
            output.write(self.document.toprettyxml(encoding='utf-8'))
