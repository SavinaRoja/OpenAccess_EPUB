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
import openaccess_epub.utils.element_methods as element_methods
from openaccess_epub.utils import OrderedSet
from .publisher_metadata import *
from collections import namedtuple
import os
import xml.dom.minidom
from lxml import etree
import logging

log = logging.getLogger('NCX')

navpoint = namedtuple('navPoint', 'id, label, playOrder, source, children')
navtarget = namedtuple('navTarget', 'id, label, source')


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
        #Create the basic document
        self.init_ncx_document()

    def init_ncx_document(self):
        """
        This method creates the initial ElementTree for the toc.ncx file
        """
        root = etree.XML('''<?xml version="1.0"?>
<!DOCTYPE ncx
  PUBLIC '-//NISO//DTD ncx 2005-1//EN'
  'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'>
<ncx version="2005-1" xml:lang="en-US" xmlns="http://www.daisy.org/z3986/2005/ncx/">
</ncx>''')
        self.document = etree.ElementTree(root)
        self.ncx = self.document.getroot()
        #The other sub elements of ncx will be created by later methods
        #These are head, docTitle, docAuthor, navMap

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
        #Pull author metadata from the article metadata for docAuthor elements
        self.extract_article_metadata()
        #Execute addition of elements to self.nav_map
        self.add_article_to_navmap()

    def add_article_to_navmap(self):
        """
        This function is responsible for adding the appropriate elements to
        the NCX file's navMap corresponding to the structure of the input
        Article. The behavior of this function differs slightly between Single
        and Collection Modes. In Single, the Title element will be at the same
        level as the top level body sections as well as the References; in
        Collection, all elements pertaining to the article will be placed as
        children of the Title element.
        """
        #Add a navpoint for the title page
        id = 'titlepage-{0}'.format(self.article_doi)
        label = self.article_title
        source = 'main.{0}.xml#title'.format(self.article_doi)
        title = navpoint(id, label, self.pull_play_order(), source, [])
        self.nav_map.append(title)
        #In Single Mode, the title will be at the same level as subsequent
        #navPoints, but in Collections, we want them to go under the title
        if self.collection_mode:
            insertion_point = title.children
        else:
            insertion_point = self.nav_map
        #Check if the article has a body element
        body = self.article.body
        if body is not None:
            self.id_int = 0
            #This step is executed as pre-processing, <sec> elements will receive
            #an id attribute if they lack one
            #This has a, helpful, side-effect when the Article is given to OPS
            for sec in body.findall('.//sec'):
                if 'id' not in sec.attrib:
                    sec.attrib['id'] = 'OA-EPUB-{0}'.format(self.id_int)
                    self.id_int += 1
            #Recursively parse the structure of the input article and add to navmap
            for nav_point in self.recursive_article_navmap(body):
                insertion_point.append(nav_point)
        #Add a navpoint for the references, if there are references
        if self.article.back is not None:
            if self.article.back.findall('ref'):
                id = 'references-{0}'.format(self.article_doi)
                label = 'References'
                source = 'biblio.{0}.xml#references'.format(self.article_doi)
                references = navpoint(id, label, self.pull_play_order(), source, [])
                insertion_point.append(references)

    def recursive_article_navmap(self, src_element, depth=0, first=True):
        """
        This function recursively traverses the content of an input article to
        add the correct elements to the NCX file's navMap and Lists.
        """
        #TODO: This may need modification for non JPTS
        if depth > self.maxdepth:
            self.maxdepth = depth
        navpoints = []
        tagnames = ['sec', 'fig', 'table-wrap']
        for child in src_element:
            try:
                tagname = child.tag
            except AttributeError:  # Text nodes have no attribute tagName
                continue
            else:
                if tagname not in tagnames:
                    continue
            source_id = child.attrib['id']
            #In single mode, use the id as it is
            if not self.collection_mode:
                child_id = source_id
            #If in collection_mode, prepend the article_doi to avoid collisions
            else:
                child_id = '{0}-{1}'.format(self.article_doi, source_id)
            #Attempt to pull the title text as a label for the navpoint
            child_title = child.find('title')
            if child_title is None:
                continue
            label = element_methods.all_text(child_title)
            if not label:
                continue
            source = 'main.{0}.xml#{1}'.format(self.article_doi, source_id)
            if tagname == 'sec':
                play_order = self.pull_play_order()
                children = self.recursive_article_navmap(child, depth=depth+1)
                new_nav = navpoint(child_id, label, play_order, source, children)
                navpoints.append(new_nav)
            #figs and table-wraps do not have children
            elif tagname == 'fig':  # Add navpoints to list_of_figures
                new_nav = navtarget(child_id, label, source)
                self.list_of_figures.append(new_nav)
            elif tagname == 'table-wrap':  # Add navpoints to list_of_tables
                new_nav = navtarget(child_id, label, source)
                self.list_of_tables.append(new_nav)
        return navpoints

    def extract_article_metadata(self):
        """
        This method calls set_publisher_metadata_methods to ensure that
        publisher-specific methods are being correctly employed. It then
        directs the acquisition of article metadata using these methods, while
        adjusting for collection_mode.
        """
        #Recall that metadata were reset in single mode during take_article
        self.set_publisher_metadata_methods()
        if self.collection_mode:
            pass  # Nothing specific to Collection Mode only at this time
        else:  # Single Mode specific actions
            pass  # Nothing specific to Single Mode only at this time

        #Generally speaking, for the NCX, little differs between Collection and
        #Single modes except for the reset between each article for Single
        #creator is OrderedSet([Creator(name, role, file_as)])
        for creator in self.get_article_creator(self.article):
            self.doc_author.add(creator)
        self.article_title = self.get_article_title(self.article)

    def set_publisher_metadata_methods(self):
        """
        Sets internal methods to be publisher specific for the article at hand.
        """
        if self.journal_doi == '10.1371':
            self.get_article_creator = plos_creator
            self.get_article_title= plos_title
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
        self.id_int = 0
        self.maxdepth = 0
        self.nav_map = []

        #Reset the other metadata and other structures
        self.reset_metadata()
        self.reset_lists()

    def reset_metadata(self):
        """
        THe NCX file does not truly exist for metadata, but it has a few
        elements held over from the Daisy Talking Book specification. The 
        """
        self.doc_author = OrderedSet()
        self.article_title = ''
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

    def make_head(self):
        """
        Creates the meta elements for the <head> section of the NCX file.
        """
        #A simple convenience function for making the meta elements
        def make_meta(content, name):
            meta = etree.Element('meta')
            meta.attrib['content'] = content
            meta.attrib['name'] = name
            return meta

        head = etree.SubElement(self.ncx, 'head')
        #Add comment about required elements
        head.append(etree.Comment('''The following metadata items, except for \
dtb:generator, are required for all NCX documents, including those conforming \
to the relaxed constraints of OPS 2.0'''))
        #Add the meta elements
        #dtb:uid - string of joined dois
        head.append(make_meta(','.join(self.all_dois), 'dtb:uid'))
        #dtb:depth - maxdepth of navMap
        head.append(make_meta(str(self.maxdepth), 'dtb:depth'))
        #dtb:totalPageCount
        head.append(make_meta('0', 'dtb:totalPageCount'))
        #dtb:maxPageNumber
        head.append(make_meta('0', 'dtb:maxPageNumber'))
        #dtb:generator
        head.append(make_meta('OpenAccess_EPUB {0}'.format(self.version),
                                   'dtb:generator'))

    def make_docTitle(self):
        """
        Creates the <docTitle> element for the NCX file.
        """
        doctitle_element = etree.SubElement(self.ncx, 'docTitle')
        text_element = etree.SubElement(doctitle_element, 'text')
        if not self.collection_mode:  # Single Mode
            #Use title of article
            text = 'NCX For: {0}'.format(self.article_title)
        else:  # Collection Mode
            #Use DOIs of all articles
            text = 'NCX For Collection: {0}'.format(','.join(self.all_dois))
        text_element.text = text

    def make_docAuthor(self):
        """
        Creates the <docAuthor> elements for the NCX file.
        """
        for author in self.doc_author:
            docauthor_element = etree.SubElement(self.ncx, 'docAuthor')
            text_element = etree.SubElement(docauthor_element, 'text')
            text_element.text = author.name

    def make_navMap(self, nav=None):
        """
        """
        #TODO: Review this method, create docstring
        if nav is None:
            nav_element = etree.Element('navMap')
            for nav_point in self.nav_map:
                nav_element.append(self.make_navMap(nav=nav_point))
        else:
            nav_element = etree.Element('navPoint')
            nav_element.attrib['id'] = nav.id
            nav_element.attrib['playOrder'] = nav.playOrder
            label_element = etree.SubElement(nav_element, 'navLabel')
            text_element = etree.SubElement(label_element, 'text')
            text_element.text = nav.label
            content_element = etree.SubElement(nav_element, 'content')
            content_element.attrib['src'] = nav.source
            for child in nav.children:
                nav_element.append(self.make_navMap(nav=child))
        return nav_element

    def make_list_of_figures(self):
        """
        Makes a navList for the NCX file representing the List of Figures.
        """
        if not self.list_of_figures:
            return
        else:
            navlist_element = etree.SubElement(self.ncx,'navList')
            navlist_element.append(self.make_navLabel('List of Figures'))
        for nav in self.list_of_figures:
            nav_target = etree.SubElement(navlist_element, 'navTarget')
            nav_target.attrib['id'] = nav.id
            nav_target.append(self.make_navLabel(nav.label))
            content_element = etree.SubElement(nav_target, 'content')
            content_element.attrib['src'] = nav.source

    def make_list_of_tables(self):
        """
        Makes a navList for the NCX file representing the List of Tables.
        """
        if not self.list_of_tables:
            return
        else:
            navlist_element = etree.SubElement(self.ncx,'navList')
            navlist_element.append(self.make_navLabel('List of Figures'))
        for nav in self.list_of_tables:
            nav_target = etree.SubElement(navlist_element, 'navTarget')
            nav_target.attrib['id'] = nav.id
            nav_target.append(self.make_navLabel(nav.label))
            content_element = etree.SubElement(nav_target, 'content')
            content_element.attrib['src'] = nav.source

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
        #Generate the content for the <head>
        self.make_head()
        #Generate the <docTitle>
        self.make_docTitle()
        #Generate the <docAuthor>(s)
        self.make_docAuthor()
        #Generate the <navMap>
        self.ncx.append(self.make_navMap())
        #Generate the List of Figures
        self.make_list_of_figures()
        #Generate the List of Tables
        self.make_list_of_tables()
        filename = os.path.join(self.location, 'OPS', 'toc.ncx')
        with open(filename, 'wb') as output:
            output.write(etree.tostring(self.document, encoding='utf-8'))

    def pull_play_order(self):
        """
        Returns the current playOrder value as string and increments it.
        """
        self.play_order += 1
        return str(self.play_order - 1)

    def use_collection_mode(self):
        """Enables Collection Mode, sets self.collection_mode to True"""
        self.collection_mode = True

    def use_single_mode(self):
        """Disables Collection Mode, sets self.collection_mode to False"""
        self.collection_mode = False

    def make_navLabel(self, text):
        """
        Creates and returns a navLabel element with the supplied text.
        """
        label_element = etree.Element('navLabel')
        text_element = etree.SubElement(label_element, 'text')
        text_element.text = text
        return label_element
