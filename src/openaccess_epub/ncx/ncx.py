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
import os
import xml.dom.minidom
import logging

log = logging.getLogger('NCX')

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
    def __init__(self):
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
        #Set internal variables to defaults
        self.reset_state()
        """

    def init_NCX_document(self):
        """
        This method creates the initial DOM document for the toc.ncx file
        """
        publicId = '-//NISO//DTD ncx 2005-1//EN'
        systemId = 'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'
        impl = xml.dom.minidom.getDOMImplementation()
        doctype = impl.createDocumentType('ncx', publicId, systemId)
        self.doc = impl.createDocument(None, 'ncx', doctype)
        self.ncx = self.doc.lastChild
        self.ncx.setAttribute('version', '2005-1')
        self.ncx.setAttribute('xml:lang', 'en-US')
        self.ncx.setAttribute('xmlns', 'http://www.daisy.org/z3986/2005/ncx/')
        #Create the sub elements to <ncx>
        ncx_subelements = ['head', 'docTitle', 'docAuthor', 'navMap']
        for element in ncx_subelements:
            self.ncx.appendChild(self.doc.createElement(element))
        self.head, self.doctitle, self.docauthor, self.navmap = self.ncx.childNodes
        #Add a label with text 'Table of Contents' to navMap
        lbl = self.appendNewElement('navLabel', self.navmap)
        lbl.appendChild(self.make_text('Table of Contents'))
        #Create some optional subelements
        #These are not added to the document yet, as they may not be needed
        self.list_of_figures = self.doc.createElement('navList')
        self.list_of_figures.setAttribute('class', 'lof')
        self.list_of_figures.setAttribute('id', 'lof')
        self.list_of_tables = self.doc.createElement('navList')
        self.list_of_tables.setAttribute('class', 'lot')
        self.list_of_tables.setAttribute('id', 'lot')
        #The <head> element requires some basic content
        self.head.appendChild(self.doc.createComment('''The following metadata
items, except for dtb:generator, are required for all NCX documents, including
those conforming to the relaxed constraints of OPS 2.0'''))
        metas = ['dtb:uid', 'dtb:depth', 'dtb:totalPageCount',
                 'dtb:maxPageNumber', 'dtb:generator']
        for meta in metas:
            meta_tag = self.doc.createElement('meta')
            meta_tag.setAttribute('name', meta)
            self.head.appendChild(meta_tag)


