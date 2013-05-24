# -*- coding: utf-8 -*-
"""
This module supplies a class for creating the toc.ncx file. The base class may
be extended by derived classes if needed. This class works with the Daisy
Talking Book specification and should work for both single and collection
output modes.
"""

import openaccess_epub.utils as utils
import os.path
import xml.dom.minidom
import logging

log = logging.getLogger('TocNCX')


class TocNCX(object):
    """
    This is the base class for the toc.ncx implementation.
    """

    def __init__(self, version, collection_mode=False):
        log.info('Instantiating TocNCX class')
        self.doi = ''
        self.dois = []
        self.collection_mode = collection_mode
        self.version = version
        self.init_NCX_document()
        #playOrder is tracked as an integer counter
        self.playOrder = 1
        #maxdepth is tracked as an integer counter
        self.maxdepth = 0
        #List of articles included
        self.articles = []

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

    def make_text(self, textstring):
        text = self.doc.createElement('text')
        text.appendChild(self.doc.createTextNode(textstring))
        return text

    def parse_article(self, article):
        """
        Process the contents of an article to build the NCX
        """
        self.doi = article.get_DOI()
        self.dois.append(self.doi)
        self.article = article
        self.a_doi = self.doi.split('/')[1]
        body = article.body
        self.articles.append(article)
        self.titlepage_navmap()
        #If we are using collection mode
        if not body:
            return
        if self.collection_mode:
            self.navmap_document_structure(body)
        #Of if not in collection mode
        else:
            self.navmap_document_structure(body)
        #Independent of mode
        if self.list_of_figures.childNodes:
            self.make_list_of_figures()
        if self.list_of_tables.childNodes:
            self.make_list_of_tables()
        self.references_navmap()

    def titlepage_navmap(self):
        """
        This is used by the navmap_document_structure method to create some elements which
        do not require structure parsing in order to create.
        """
        #The title page element we will always expect
        nav = self.appendNewElement('navPoint', self.navmap)
        if self.collection_mode:
            nav.setAttribute('id', 'titlepage-{0}'.format(self.a_doi))
        else:
            nav.setAttribute('id', 'titlepage')
        nav.setAttribute('playOrder', str(self.playOrder))
        self.playOrder += 1
        navlbl = self.appendNewElement('navLabel', nav)
        navlbl.appendChild(self.make_text('Title'))
        navcon = self.appendNewElement('content', nav)
        navcon.setAttribute('src', 'main.{0}.xml#title'.format(self.a_doi))

    def references_navmap(self):
        """
        The references page should be added if there are references, this is
        used by the navmap_document_structure method
        """
        try:
            back = self.article.root_tag.getElementsByTagName('back')[0]
        except IndexError:
            pass
        else:
            if back.getElementsByTagName('ref'):
                nav = self.appendNewElement('navPoint', self.navmap)
                if self.collection_mode:
                    nav.setAttribute('id', 'references-{0}'.format(self.a_doi))
                else:
                    nav.setAttribute('id', 'references')
                nav.setAttribute('playOrder', str(self.playOrder))
                self.playOrder += 1
                navlbl = self.appendNewElement('navLabel', nav)
                navlbl.appendChild(self.make_text('References'))
                navcon = self.appendNewElement('content', nav)
                artdoi = self.doi.split('/')[1]
                navcon.setAttribute('src', 'biblio.{0}.xml#references'.format(artdoi))

    def navmap_document_structure(self, srcnode, dstnode=None, depth=0, first=True):
        """
        This recursive function travels the contents of an article's body node
        looking for <sec>, <fig>, and <table-wrap> tags. It only locates these
        tags when they are the children of <body> or another tag. This is as it
        should be in properly formatted input.
        """
        #We only really care about the recursion depth because we need to list
        #it in the NCX meta elements.
        depth += 1
        if depth > self.maxdepth:
            self.maxdepth = depth
        if not dstnode:
            dstnode = self.navmap
        #Tag name strings we check for to determine structures and features
        tagnames = ['sec', 'fig', 'table-wrap']
        #Pre-process step: give sec tags an id attribute if they lack it
        c = 0
        for sec in srcnode.getElementsByTagName('sec'):
            if not sec.getAttribute('id'):
                sid = 'OA-EPUB-{0}'.format(str(c))
                c += 1
                sec.setAttribute('id', sid)
        #Do the recursive parsing
        for child in srcnode.childNodes:
            try:
                tagname = child.tagName
            except AttributeError:  # Text nodes have no attribute tagName
                pass
            else:
                if tagname in tagnames:
                    if tagname == 'sec':
                        nav = self.doc.createElement('navPoint')
                        dstnode.appendChild(nav)
                    elif tagname == 'fig':
                        nav = self.doc.createElement('navTarget')
                        self.list_of_figures.appendChild(nav)
                    elif tagname == 'table-wrap':
                        if not child.getChildrenByTagName('alternatives') and not child.getChildrenByTagName('graphic'):
                            continue
                        nav = self.doc.createElement('navTarget')
                        self.list_of_tables.appendChild(nav)
                    mid = child.getAttribute('id')
                    if self.collection_mode:
                        nav.setAttribute('id', '{0}-{1}'.format(self.a_doi, mid))
                    else:
                        nav.setAttribute('id', mid)
                    nav.setAttribute('playOrder', str(self.playOrder))
                    self.playOrder += 1
                    navlbl = nav.appendChild(self.doc.createElement('navLabel'))
                    try:
                        title_node = child.getElementsByTagName('title')[0]
                    except IndexError:  # For whatever reason, no title node
                        navlblstr = 'Item title not found!'
                    else:
                        navlblstr = utils.serializeText(title_node, stringlist=[])
                        if not navlblstr:
                            navlblstr = mid
                    navlbl.appendChild(self.make_text(navlblstr))
                    navcon = nav.appendChild(self.doc.createElement('content'))
                    navcon.setAttribute('src', 'main.{0}.xml#{1}'.format(self.a_doi, mid))
                    self.navmap_document_structure(child, nav, depth, first=False)
        #self.references_navmap()

    def make_doctitle(self):
        """
        Fills in the <docTitle> node, works for both single and collection
        mode.
        """
        if self.collection_mode:
            tocname = 'NCX For: Article Collection'
            self.doctitle.appendChild(self.make_text(tocname))
        else:
            tocname = 'NCX For: {0}'.format(self.doi)
            self.doctitle.appendChild(self.make_text(tocname))

    def make_docauthor(self):
        """
        Fills in the <docAuthor> node.
        mode.
        """
        #Technically, the best practice for this tag is to match its
        #counterpart in the OPF file. This get's hazy with regards to multiple
        #authors and especially in the case of multiple articles. Previously
        #this employed the first author of the first article and, I will
        #probably adjust it back to that eventually.
        authlabel = 'Paul Barton, Developer of OpenAccess_EPUB'
        self.docauthor.appendChild(self.make_text(authlabel))

    def appendNewElement(self, newelement, parent):
        """
        A common idiom is to create an element and then immediately append it
        to another. This method allows that to be done more concisely. It
        returns the newly created and appended element.
        """
        new = self.doc.createElement(newelement)
        parent.appendChild(new)
        return new

    def appendNewText(self, newtext, parent):
        """
        A common idiom is to create a new text node and then immediately append
        it to another element. This method makes that more concise. It does not
        return the newly created and appended text node
        """
        new = self.doc.createTextNode(newtext)
        parent.appendChild(new)

    def set_metas(self):
        """
        After all the articles have been processed, this method provides values
        to each of the meta items.
        """
        metas = self.head.getElementsByTagName('meta')
        for meta in metas:
            if meta.getAttribute('name') == 'dtb:depth':
                meta.setAttribute('content', str(self.maxdepth - 1))
            elif meta.getAttribute('name') == 'dtb:uid':
                meta.setAttribute('content', ','.join(self.dois))
            elif meta.getAttribute('name') == 'dtb:generator':
                content = 'OpenAccess_EPUB {0}'.format(self.version)
                meta.setAttribute('content', content)
            else:
                meta.setAttribute('content', '0')

    def make_list_of_figures(self):
        """
        Prepends the List of Figures with appropriate navLabel and adds the
        element to the ncx element
        """
        navlbl = self.doc.createElement('navLabel')
        navlbl.appendChild(self.make_text('List of Figures'))
        self.list_of_figures.insertBefore(navlbl, self.list_of_figures.firstChild)
        self.ncx.appendChild(self.list_of_figures)

    def make_list_of_tables(self):
        """
        Prepends the List of Tables with appropriate navLabel and adds the
        element to the ncx element
        """
        navlbl = self.doc.createElement('navLabel')
        navlbl.appendChild(self.make_text('List of Tables'))
        self.list_of_tables.insertBefore(navlbl, self.list_of_tables.firstChild)
        self.ncx.appendChild(self.list_of_tables)

    def write(self, location):
        """
        This method defines how the document should be written. It calls the
        necessary functions required to finalize the document and then writes
        the file to disk.
        """
        self.set_metas()
        self.make_docauthor()
        self.make_doctitle()
        filename = os.path.join(location, 'OPS', 'toc.ncx')
        with open(filename, 'wb') as output:
            output.write(self.doc.toprettyxml(encoding='utf-8'))
