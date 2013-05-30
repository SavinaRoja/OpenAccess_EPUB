# -*- coding: utf-8 -*-
"""
This module provides the basic tools necessary to create the NCX (Navigation
Center eXtended) file for ePub. The specification for this file is a subsection
of the OPF specification. See:

http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.4.1
http://www.niso.org/workrooms/daisy/Z39-86-2005.html#NCX

The NCX file is REQUIRED for valid ePub, but readers support it OPTIONALLY. Its
job is to provide a more advanced Table of Contents-style navigation system for
the ePub beyond what is done in the OPF file.
"""

import openaccess_epub.utils as utils
from openaccess_epub.utils import OrderedSet
from .publisher_metadata import *
from collections import namedtuple
import os
import xml.dom.minidom
import logging

log = logging.getLogger('NCX')

navpoint = namedtuple('navPoint', 'id, label, playOrder, source')

class NCX(object):
    """
    This class represents the NCX file, its generation with input, and its
    output rendering.

    The NCX serves to provide additional Table of Contents-style navigation
    through the ePub file.

    When the NCX class initiates, it contains no content, creating only the
    basic file framework and static data. To pass input articles to the NCX
    class, whether for Single Input Mode or for Collection Mode, use the
    OPF.take_article method.

    Similar to the opf.OPF class, the NCX class maintains a notion of internal
    state. This gives it focus on a single input article at a time,
    incorporating what it needs from the content data to generate internal data
    structures. This model serves as a framework that makes Collection Mode
    much easier and makes cross-journal support possible; it makes little
    difference to Single Input unless one is using an unusual workflow (such as
    using the same NCX instance to generate .ncx files for different ePubs).
    """
    def __init__(self, oae_version, location=os.getcwd(),
                  collection_mode=False):
        """
        Initialization arguments:
            oae_version - Version of OpenAccess_Epub; needed to specify in the
              header what version of OAE generated the toc.ncx file
            location - Where this ePub is based
            collection_mode - To use Collection Mode, set to True

        Collection Mode can be turned on or off after initialization using the
        use_collection_mode() and use_single_mode methods() respectively.
e
        before writing will give it a title.
        """
        #Set internal variables to defaults
        self.reset_state()
        #Pull in argument values
        self.version = oae_version
        self.location = location
        self.collection_mode = collection_mode

    def init_NCX_document(self):
        """
        This method creates the initial DOM document for the toc.ncx file
        """
        publicId = '-//NISO//DTD ncx 2005-1//EN'
        systemId = 'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'
        impl = xml.dom.minidom.getDOMImplementation()
        doctype = impl.createDocumentType('ncx', publicId, systemId)
        self.doc = impl.createDocument(None, 'ncx', doctype)
        self.ncx = self.document.lastChild
        self.ncx.setAttribute('version', '2005-1')
        self.ncx.setAttribute('xml:lang', 'en-US')
        self.ncx.setAttribute('xmlns', 'http://www.daisy.org/z3986/2005/ncx/')
        #Create the sub elements to <ncx>
        ncx_subelements = ['head', 'docTitle', 'docAuthor', 'navMap']
        for element in ncx_subelements:
            self.ncx.appendChild(self.document.createElement(element))
        self.head, self.doctitle, self.docauthor, self.navmap = self.ncx.childNodes
        #Add a label with text 'Table of Contents' to navMap
        lbl = self.appendNewElement('navLabel', self.navmap)
        lbl.appendChild(self.make_text('Table of Contents'))
        #Create some optional subelements
        #These are not added to the document yet, as they may not be needed
        #self.list_of_figures = self.document.createElement('navList')
        #self.list_of_figures.setAttribute('class', 'lof')
        #self.list_of_figures.setAttribute('id', 'lof')
        #self.list_of_tables = self.document.createElement('navList')
        #self.list_of_tables.setAttribute('class', 'lot')
        #self.list_of_tables.setAttribute('id', 'lot')
        #The <head> element requires some basic content
        self.head.appendChild(self.document.createComment('''The following metadata
items, except for dtb:generator, are required for all NCX documents, including
those conforming to the relaxed constraints of OPS 2.0'''))
        metas = ['dtb:uid', 'dtb:depth', 'dtb:totalPageCount',
                 'dtb:maxPageNumber', 'dtb:generator']
        for meta in metas:
            meta_tag = self.document.createElement('meta')
            meta_tag.setAttribute('name', meta)
            self.head.appendChild(meta_tag)

    def take_article(self, article):
        """
        Receives an instance of the Article class. This modifies the internal
        state of the NCX class to focus on the new article for the purposes of
        extracting structural information, and the article authors as metadata.
        
        In Collection Mode, the addition of new articles to the NCX class
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
        #Recursively parse the structure of the input article and add to navmap
        self.recursive_article_navmap()
        #Pull author metadata from the article metadata for docAuthor elements
        self.extract_article_authors()

    def extract_article_authors(self):
        """
        This method calls set_publisher_author_methods to ensure that
        publisher-specific methods are being correctly employed. It then
        directs the acquisition of article metadata using these methods, while
        adjusting for collection_mode.
        """
        #Recall that metadata were reset in single mode during take_article
        self.set_publisher_author_methods()
        if self.collection_mode(self):
            pass  # Nothing specific to Collection Mode only at this time
        else:  # Single Mode specific actions
            pass  # Nothing specific to Single Mode only at this time

        #These are no different between Single and Collection Modes
        #Generally speaking, for the NCX, little differs between Collection and
        #Single modes except for the reset between each article for Single
        #creator is OrderedSet([Creator(name, role, file_as)])
        for creator in self.get_article_creator(self.article):
            self.doc_author.add(creator)

    def set_publisher_author_methods(self):
        """
        Sets internal methods to be publisher specific for the article at hand.
        """
        if self.journal_doi == '10.1371':
            self.get_article_creator = plos_creator
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
        self.play_order = 1

        #Reset the other metadata and other structures
        self.reset_metadata()
        self.reset_lists()

    def reset_metadata():
        """
        THe NCX file does not truly exist for metadata, but it has a few
        elements held over from the Daisy Talking Book specification. The 
        """
        self.doc_author = OrderedSet()
        #The docTitle can be auto-generated from self.all_articles, so there is
        #no need to collect anything else

    def reset_lists(self):
        """
        Resets the internal states of the lists of items: List of Figures, List
        of Tables, and List of Equations. This is distinct from the navMap.
        """
        self.list_of_figures = []
        self.list_of_tables = []
        self.list_of_equations = []

    def write(self):
        """
        Writing the NCX file is immediately preceded by jobs that finalize
        the NCX document. This includes the creation of the navMap, the
        generation and creation of meta elements in the head, and the navList
        elements.

        Writing the NCX file should be done after all intended input articles
        have been passed in. This will be one of the final steps of the ePub
        creation process.
        """
        filename = os.path.join(self.location, 'OPS', 'content.opf')
        with open(filename, 'wb') as output:
            output.write(self.document.toprettyxml(encoding='utf-8'))

    def use_collection_mode(self):
        """Enables Collection Mode, sets self.collection_mode to True"""
        self.collection_mode = True

    def use_single_mode(self):
        """Disables Collection Mode, sets self.collection_mode to False"""
        self.collection_mode = False

