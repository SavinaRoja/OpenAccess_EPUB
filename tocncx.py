import utils
import os.path
from xml.dom.minidom import getDOMImplementation
import main
    
class tocNCX(object):
    '''A class to represent the Table of Contents NCX. Should be versatile in 
    use for all ePub creation modes. Should be kept in accordance with the 
    Daisy Talking Book specification.'''
    
    def __init__(self, collection_mode = False):
        self.collection_mode = collection_mode
        #Make a DOM implementation of our file
        _publicId = '-//NISO//DTD ncx 2005-1//EN'
        _systemId = 'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'
        
        impl = getDOMImplementation()
        mytype = impl.createDocumentType('ncx', _publicId, _systemId)
        self.toc = impl.createDocument(None, 'ncx', mytype)
        
        self.ncx = self.toc.lastChild #IGNORE:E1101
        self.ncx.setAttribute('version', '2005-1')
        self.ncx.setAttribute('xml:lang', 'en-US')
        self.ncx.setAttribute('xmlns', 'http://www.daisy.org/z3986/2005/ncx/')
        #Create the sub elements to <ncx>
        ncx_subelements = ['head', 'docTitle', 'docAuthor', 'navMap']
        for element in ncx_subelements:
            self.ncx.appendChild(self.toc.createElement(element))
        self.head, self.doctitle, self.docauthor, self.navmap = self.ncx.childNodes
        #Create some optional subelements
        self.lof = self.toc.createElement('navList')
        self.lof.setAttribute('class', 'lof')
        self.lof.setAttribute('id', 'lof')
        self.lot = self.toc.createElement('navList')
        self.lot.setAttribute('class', 'lot')
        self.lot.setAttribute('id', 'lot')
        #The <head> element requires some base content
        self.head.appendChild(self.toc.createComment('''The following metadata 
items, except for dtb:generator, are required for all NCX documents, including 
those conforming to the relaxed constraints of OPS 2.0'''))
        metas = ['dtb:uid', 'dtb:depth','dtb:totalPageCount', 
                 'dtb:maxPageNumber', 'dtb:generator']
        for meta in metas:
            meta_tag = self.toc.createElement('meta')
            meta_tag.setAttribute('name', meta)
            self.head.appendChild(meta_tag)
        #Some important integers
        self.playOrder = 1
        self.maxdepth = 0
        #List of articles included
        self.articles = []
    
    def takeArticle(self, article):
        '''Process the contents of an article to build the NCX'''
        self.articles += [article]
        front = article.front
        body = article.body
        #If we are only packing one article...
        if not self.collection_mode:
            #Using the body node, construct the navMap and other lists
            lbl = self.toc.createElement('navLabel')
            lbl.appendChild(self.makeText('Table of Contents'))
            self.navmap.appendChild(lbl)
            self.structureParse(article.body)
            if self.lof.childNodes:
                self.makeFiguresList()
            if self.lot.childNodes:
                self.makeTablesList()
            #Set the metas with self.setMetas()
            self.setMetas()
            #Set the docAuthor and docTitle nodes
            self.makeDocAuthor()
            self.makeDocTitle()
        #If we are packing arbitrarily many articles...
        else:
            #Place the article title into <docTitle>
            titletext = 'Custom Collection'
            tocname = u'NCX For: {0}'.format(titletext)
            self.doctitle.appendChild(self.makeText(tocname))
            #For <docAuthor>, I guess 
    
    def structureParse(self, srcnode, dstnode = None, depth = 0, first = True):
        '''The structure of an article's <body> content can be analyzed in 
        terms of nested <sec> tags, along with features like <fig> and 
        <table-wrap>.'''
        depth += 1
        if depth > self.maxdepth:
            self.maxdepth = depth
        if not dstnode:
            dstnode = self.navmap
        #We build the first structure element, it is not found in article.body
        if first:
            nav = dstnode.appendChild(self.toc.createElement('navPoint'))
            nav.setAttribute('id', 'titlepage')
            nav.setAttribute('playOrder', str(self.playOrder))
            self.playOrder += 1
            navlbl = nav.appendChild(self.toc.createElement('navLabel'))
            navlbl.appendChild(self.makeText('Title Page'))
            navcon = nav.appendChild(self.toc.createElement('content'))
            navcon.setAttribute('src','synop.xml#title')
        #Tag name strings we check for to determine structures and features
        tagnamestrs = [u'sec', u'fig', u'table-wrap']
        #Do the recursive parsing
        for child in srcnode.childNodes:
            try:
                tagname = child.tagName
            except AttributeError: #Text nodes have no attribute tagName
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
                    id = child.getAttribute('id')
                    nav.setAttribute('id', id)
                    nav.setAttribute('playOrder', str(self.playOrder))
                    self.playOrder += 1
                    navlbl = nav.appendChild(self.toc.createElement('navLabel'))
                    try:
                        title_node = child.getElementsByTagName('title')[0]
                    except IndexError: #For whatever reason, no title node
                        navlblstr = 'Item title not found!'
                    else:
                        navlblstr = utils.serializeText(title_node, stringlist = [])
                    navlbl.appendChild(self.makeText(navlblstr))
                    navcon = nav.appendChild(self.toc.createElement('content'))
                    navcon.setAttribute('src', 'main.xml#{0}'.format(id))
                    self.structureParse(child, nav, depth, first = False)
    
    def makeDocTitle(self):
        '''Fills in the <docTitle> node, works for both single and collection 
        mode.'''
        if not self.collection_mode:
            article = self.articles[0]
            front = article.front
            titletext = utils.serializeText(front.article_meta.article_title, stringlist = [])
            tocname = u'NCX For: {0}'.format(titletext)
            self.doctitle.appendChild(self.makeText(tocname))
        else:
            tocname = u'NCX For: PLoS Article Collection'
            self.doctitle.appendChild(tocname)
    
    def makeDocAuthor(self):
        '''Fills in the <docAuthor> node, works for both single and collection 
        mode.'''
        if not self.collection_mode:
            article = self.articles[0]
            front = article.front
            authortext = front.article_meta.art_auths[0].get_name()
            authlabel = u'Primary author: {0}'.format(authortext)
            self.docauthor.appendChild(self.makeText(authlabel))
        else:
            article = self.articles[0]
            front = article.front
            authortext = front.article_meta.art_auths[0].get_name()
            authlabel = u'Primary author of first paper: {0}'.format(authortext)
            self.docauthor.appendChild(self.makeText(authlabel))
    
    def write(self, location):
        filename = os.path.join(location, 'OPS', 'toc.ncx')
        with open(filename, 'w') as output:
            output.write(self.toc.toprettyxml(encoding = 'utf-8'))
    
    def makeText(self, textstring):
        text = self.toc.createElement('text')
        text.appendChild(self.toc.createTextNode(textstring))
        return text
    
    def setMetas(self):
        '''Provides attribute values to the four required meta elements.'''
        metas = self.head.getElementsByTagName('meta')
        for meta in metas:
            if meta.getAttribute('name') == 'dtb:depth':
                meta.setAttribute('content', str(self.maxdepth - 1))
            elif meta.getAttribute('name') == 'dtb:uid':
                if not self.collection_mode:
                    ids = self.articles[0].front.article_meta.identifiers
                    for (_data, _id) in ids:
                        if _id == 'doi':
                            uid = _data
                    meta.setAttribute('content', uid)
                else:
                    meta.setAttribute('content', '10.1371')
            elif meta.getAttribute('name') == 'dtb:generator':
                content = 'OpenAccess_EPUB {0}'.format(main.__version__)
                meta.setAttribute('content', content)
            else:
                meta.setAttribute('content', '0')
    
    def makeFiguresList(self):
        '''Prepends the List of Figures with appropriate navLabel and adds the 
        element to the ncx element'''
        navlbl = self.toc.createElement('navLabel')
        navlbl.appendChild(self.makeText('List of Figures'))
        self.lof.insertBefore(navlbl, self.lof.firstChild)
        self.ncx.appendChild(self.lof)
    
    def makeTablesList(self):
        '''Prepends the List of Tables with appropriate navLabel and adds the 
        element to the ncx element'''
        navlbl = self.toc.createElement('navLabel')
        navlbl.appendChild(self.makeText('List of Tables'))
        self.lot.insertBefore(navlbl, self.lot.firstChild)
        self.ncx.appendChild(self.lot)