import logging
from utils import getTagData

class BodyMatter(object):
    '''Body matter of the article, along with important handling functions'''
    def __init__(self, body, doc):
        
        self.secdepth = 0
        self.maxdepth = 0
        
        def dirtySecs(parentnode, oldnode):
            for n in parentnode.childNodes:
                if n.localName == 'sec':
                    newnode = doc.createElement(n.getAttribute('id'))
                    oldnode.appendChild(newnode)
                    dirtySecs(n,newnode)
            return oldnode
            
        self.secnodemap = dirtySecs(body, doc.createElement('secnodemap'))
        logging.debug(self.secnodemap.toprettyxml())
        
        self.playOrder = 1
        
        def kinkySecs(parentnode, oldnode, orderint):
            for n in parentnode.childNodes:
                if n.localName == 'sec':
                    newnode = doc.createElement('sec')
                    newnode.setAttribute('id', n.getAttribute('id'))
                    newnode.setAttribute('navLabel', getTagData(n.getElementsByTagName('title')))
                    newnode.setAttribute('playOrder', str(self.playOrder))
                    oldnode.appendChild(newnode)
                    self.playOrder += 1
                    kinkySecs(n, newnode, self.playOrder)
                if n.localName == 'fig':
                    newnode = doc.createElement('fig')
                    newnode.setAttribute('id', n.getAttribute('id'))
                    newnode.setAttribute('navLabel', getTagData(n.getElementsByTagName('label')))
                    newnode.setAttribute('playOrder', str(self.playOrder))
                    oldnode.appendChild(newnode)
                    self.playOrder += 1
                    kinkySecs(n, newnode, self.playOrder)
                if n.localName == 'table-wrap':
                    newnode = doc.createElement('table-wrap')
                    newnode.setAttribute('id', n.getAttribute('id'))
                    newnode.setAttribute('navLabel', getTagData(n.getElementsByTagName('label')))
                    newnode.setAttribute('playOrder', str(self.playOrder))
                    oldnode.appendChild(newnode)
                    self.playOrder += 1
                    kinkySecs(n, newnode, self.playOrder)
                    
        self.kinkymap = doc.createElement('kinkymap')
        kinkySecs(body, self.kinkymap, self.playOrder)
        print(self.kinkymap.toprettyxml())