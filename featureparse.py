from HTMLParser import HTMLParser
from xml.dom.minidom import getDOMImplementation

class featureParse(HTMLParser):
    ''''''
    def __init__(self, bodynode):
        self.depth = 0
        self.max_depth = self.depth
        self.playorder_track = 1
        
        self.tagname = None
        self.tagattrs = None
        
        self.currentsec = None
        self.secfound = False
        self.sectitlefound = False
        
        
        impl = getDOMImplementation()
        self.mydoc = impl.createDocument(None, 'featureParse', None)
        
        self.navtree = self.mydoc.lastChild
        
        HTMLParser.__init__(self)
        self.feed(bodynode.toxml())
        
    def handle_starttag(self, tag, attrs):
        if tag == u'sec':
            self.tagname, self.tagattrs = tag, attrs
            self.depth += 1
            self.secfound = True
            
        if self.secfound:
            if tag == u'title':
                self.secfound = False
                self.sectitlefound = True
                
            
    def handle_data(self, data):
        if self.sectitlefound:
            self.createNode(self.tagname, self.tagattrs, data)
            self.playorder_track += 1
            self.sectitlefound = False
        
    def handle_endtag(self, tag):
        if tag == u'/sec':
            self.depth -= 1
        
        
    def createNode(self, tagname, attrs, data):
        newnode = self.mydoc.createElement('navPoint')
        newnode.setAttribute('playOrder', self.playorder_track)
        for _name, _value in attrs:
            if _name == u'id':
                newnode.setAttribute(_name, _value)
        if tagname == u'sec':
            newnode.setAttribute('class', 'section')
        label = newnode.appendChild(self.mydoc.createElement('navLabel'))
        text = label.appendChild(self.mydoc.createElement('text'))
        text.appendChild(self.mydoc.createTextNode(data))
        
import xml.dom.minidom as minidom

doc = minidom.parse('test_data/article.xml')
body = doc.getElementsByTagName('body')[0]
featureParse(body)
