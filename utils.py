"""utility/common stuff"""
import logging
import os.path
from collections import namedtuple

#OUT_DIR = 'test_output'

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

Identifier = namedtuple('Identifer', 'id, type')

def createDCElement(document, name, data, attributes = None):
    '''A convenience method for creating DC tag elements.
    Used in content.opf'''
    newnode = document.createElement(name)
    newnode.appendChild(document.createTextNode(data))
    if attributes:
        for attr, attrval in attributes.iteritems():
            newnode.setAttribute(attr, attrval)
    
    return newnode

def stripDOMLayer(oldnodelist, depth = 1):
    '''This method strips layers \"off the top\" from a specified NodeList or 
    Node in the DOM. All child Nodes below the stripped layers are returned as
    a NodeList, treating them as siblings irrespective of the original 
    hierarchy. To be used with caution. '''
    newnodelist = []
    while depth:
        try:
            for child in oldnodelist:
                newnodelist += child.childNodes
                
        except TypeError:
            newnodelist = oldnodelist.childNodes
            
        depth -= 1
        newnodelist = stripDOMLayer(newnodelist, depth)
        return newnodelist
    return oldnodelist

def serializeText(fromnode, stringlist = [], sep = u''):
    '''Recursively extract the text data from a node and it's children'''
    for item in fromnode.childNodes:
        if item.nodeType == item.TEXT_NODE and not item.data == u'\n':
            stringlist.append(item.data)
        else:
            serializeText(item, stringlist, sep)
    return sep.join(stringlist)
    
def getTagText(node):
    '''Grab the text data from a Node. If it is provided a NodeList, it will 
    return the text data from the first contained Node.'''
    data = u''
    try :
        children = node.childNodes
    except AttributeError:
        getTagText(node[0])
    else:
        if children:
            for child in children:
                if child.nodeType == child.TEXT_NODE and not child.data == u'\n':
                    data = child.data
            return data
    
def getTagData(node_list):
    """Grab the (string) data from text elements
    node_list -- NodeList returned by getElementsByTagName
    """
    data = u''
    try:
        for node in node_list:
            if node.firstChild.nodeType == node.TEXT_NODE:
                data = node.firstChild.data
        return data
    except TypeError:
        getTagData([node_list])

def recursive_zip(zipf, directory, folder = ""):
    '''Recursively traverses the output directory to construct the zipfile'''
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), os.path.join(directory,
                                                                   item))
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(zipf, os.path.join(directory, item),
                          os.path.join(folder, item))
    

def initiateDocument(titlestring,
                     _publicId = '-//W3C//DTD XHTML 1.1//EN',
                     _systemId = 'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'):
    '''A method for conveniently initiating a new xml.DOM Document'''
    from xml.dom.minidom import getDOMImplementation
    
    impl = getDOMImplementation()
    
    mytype = impl.createDocumentType('article', _publicId, _systemId)
    doc = impl.createDocument(None, 'root', mytype)
    
    root = doc.lastChild #IGNORE:E1101
    root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
    root.setAttribute('xml:lang', 'en-US')
    
    head = doc.createElement('head')
    root.appendChild(head)
    
    title = doc.createElement('title')
    title.appendChild(doc.createTextNode(titlestring))
    
    link = doc.createElement('link')
    link.setAttribute('rel', 'stylesheet')
    link.setAttribute('href','css/reference.css')
    link.setAttribute('type', 'text/css')
    
    meta = doc.createElement('meta')
    meta.setAttribute('http-equiv', 'Content-Type')
    meta.setAttribute('content', 'application/xhtml+xml')
    meta.setAttribute('charset', 'utf-8')
    
    headlist = [title, link, meta]
    for tag in headlist:
        head.appendChild(tag)
    root.appendChild(head)
    
    body = doc.createElement('body')
    root.appendChild(body)
    
    return doc, body