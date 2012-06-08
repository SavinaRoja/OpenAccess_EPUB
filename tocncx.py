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

    def __init__(self, version, collection_mode=False):
        self.dois = []
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

    def parseArticle(self):
        """
        pass
        """
        self.dois.append(doi)

    def indexTitlePage(self):
        """
        This is used to create a reference in the navMap of the NCX file to the
        titlepage of the article.
        """
        pass

    def structureParse(self, srcnode, dstnode=self.navmap, depth=0, first=True):
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
        #We build the first structure element, it is not found in article.body
        if first:
            nav = dstnode.appendChild(self.toc.createElement('navPoint'))
            nav.setAttribute('id', 'titlepage')
            nav.setAttribute('playOrder', str(self.playOrder))
            self.playOrder += 1
            navlbl = nav.appendChild(self.toc.createElement('navLabel'))
            navlbl.appendChild(self.makeText('Title Page'))
            navcon = nav.appendChild(self.toc.createElement('content'))
            navcon.setAttribute('src', 'synop.{0}.xml#title'.format(self.jid))
        #Tag name strings we check for to determine structures and features
        tagnamestrs = [u'sec', u'fig', u'table-wrap']
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
                if tagname in tagnamestrs:
                    if tagname == u'sec':
                        nav = self.toc.createElement('navPoint')
                        dstnode.appendChild(nav)
                    elif tagname == u'fig':
                        nav = self.toc.createElement('navTarget')
                        self.lof.appendChild(nav)
                    elif tagname == u'table-wrap':
                        nav = self.toc.createElement('navTarget')
                        self.lot.appendChild(nav)
                    mid = child.getAttribute('id')
                    nav.setAttribute('id', mid)
                    nav.setAttribute('playOrder', str(self.playOrder))
                    self.playOrder += 1
                    navlbl = nav.appendChild(self.toc.createElement('navLabel'))
                    try:
                        title_node = child.getElementsByTagName('title')[0]
                    except IndexError:  # For whatever reason, no title node
                        navlblstr = 'Item title not found!'
                    else:
                        navlblstr = utils.serializeText(title_node, stringlist=[])
                        if not navlblstr:
                            navlblstr = mid
                    navlbl.appendChild(self.makeText(navlblstr))
                    navcon = nav.appendChild(self.toc.createElement('content'))
                    navcon.setAttribute('src', 'main.{0}.xml#{1}'.format(self.jid, mid))
                    self.structureParse(child, nav, depth, first = False)

    def makeDocTitle(self):
        """
        Fills in the <docTitle> node, works for both single and collection
        mode.
        """
        if self.collection_mode:
            tocname = 'NCX For: Article Collection'
            self.doctitle.appendChild(self.makeText(tocname))
        else:
            tocname = u'NCX For: '.format(self.doi[0])
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

    def setMetas(self):
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

    def write(self, location):
        self.setMetas()
        self.makeDocAuthor()
        self.makeDocTitle()
        filename = os.path.join(location, 'OPS', 'toc.ncx')
        with open(filename, 'w') as output:
            output.write(self.toc.toprettyxml('utf-8'))
