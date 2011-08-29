"""utility/common stuff"""
import logging
import os.path
from collections import namedtuple

OUT_DIR = 'test_output'

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

Identifier = namedtuple('Identifer', 'id, type')

def getTagData(node_list):
    """Grab the (string) data from text elements
    node_list -- NodeList returned by getElementsByTagName
    """
    data = u''
    for node in node_list:
        if node.firstChild.nodeType == node.TEXT_NODE:
            data = node.firstChild.data
    return data

def recursive_zip(zipf, directory, folder = ""):
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), os.path.join(directory, item))
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(zipf, os.path.join(directory, item), os.path.join(folder, item))
    

def initiateDocument(titlestring,
                     _publicId = '-//W3C//DTD XHTML 1.1//EN',
                     _systemId = 'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd',):
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