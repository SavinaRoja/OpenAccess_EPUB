"""
This module supplies a class for creating the toc.ncx file. The base class may
be extended by derived classes if needed. This class works with the Daisy
Talking Book specification and should work for both single and collection
output modes.
"""

import utils
import os.path
import xml.dom.minidom


class TocNCX(object):
    """
    This is the base class for the toc.ncx implementation.
    """

    def __init__(self, version, doi, collection_mode=False):
        self.doi = doi
        self.collection_mode = collection_mode
        self.version = version
        self.initNcxDocument()
        #playOrder is tracked as an integer counter
        self.playOrder = 1
        #maxdepth is tracked as an integer counter
        self.maxdepth = 0
        #List of articles included
        self.articles = []

    def initNcxDocument(self):
        """
        This method creates the initial DOM document for the toc.ncx file
        """
        publicId = '-//NISO//DTD ncx 2005-1//EN'
        systemId = 'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'
        impl = xml.dom.minidom.getDOMImplementation
        doctype = impl.createDocumentType('ncx', publicId, systemId)
        self.doc = impl.createDocument(None, 'ncx', doctype)
        self.ncx = self.doc.lastChild
        self.ncx.setAttribute('version', '2005-1')
        self.ncx.setAttribute('xml:lang', 'en-US')
        self.ncx.setAttribute('xmlns', 'http://www.daisy.org/z3986/2005/ncx/')
        #Create the sub elements to <ncx>
        ncx_subelements = ['head', 'docTitle', 'docAuthor', 'navMap']
        for element in ncx_subelements:
            self.ncx.appendChild(self.toc.createElement(element))
        self.head, self.doctitle, self.docauthor, self.navmap = self.ncx.childNodes
        #Add a label with text 'Table of Contents' to navMap
        lbl = self.appendNewElement('navLabel', self.navmap)
        lbl.appendChild(self.makeText('Table of Contents'))
        #Create some optional subelements
        #These are not added to the document yet, as they may not be needed
        self.lof = self.toc.createElement('navList')
        self.lof.setAttribute('class', 'lof')
        self.lof.setAttribute('id', 'lof')
        self.lot = self.toc.createElement('navList')
        self.lot.setAttribute('class', 'lot')
        self.lot.setAttribute('id', 'lot')
        #The <head> element requires some basic content
        self.head.appendChild(self.toc.createComment('''The following metadata
items, except for dtb:generator, are required for all NCX documents, including
those conforming to the relaxed constraints of OPS 2.0'''))
        metas = ['dtb:uid', 'dtb:depth', 'dtb:totalPageCount',
                 'dtb:maxPageNumber', 'dtb:generator']
        for meta in metas:
            meta_tag = self.toc.createElement('meta')
            meta_tag.setAttribute('name', meta)
            self.head.appendChild(meta_tag)

    def makeText(self, textstring):
        text = self.toc.createElement('text')
        text.appendChild(self.toc.createTextNode(textstring))
        return text

    def makeDocTitle(self):
        """
        Fills in the <docTitle> node, works for both single and collection
        mode.
        """
        if self.collection_mode:
            tocname = 'NCX For: Article Collection'
            self.doctitle.appendChild(self.makeText(tocname))
        else:
            tocname = u'NCX For: '.format(self.doi)
            self.doctitle.appendChild(self.makeText(tocname))

    def makeDocAuthor(self):
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
        self.docauthor.appendChild(self.makeText(authlabel))

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



