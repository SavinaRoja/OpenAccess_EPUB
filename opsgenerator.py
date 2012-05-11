"""
This module defines a base class for the generation of Open Publication
Structure content. These tools facilitate the creation of OPS documents
independent of tag set version or publisher. This class is not a full-featured
translator from any XML format to OPS XML for ePub; derived classes for each
tag set and/or publisher must provide these functions.
"""

import xml.dom.minidom


class OPSGenerator(object):
    """
    This class provides several baseline features and functions required in
    order to produce OPS content.
    """
    def __init__(self):
        print('Instantiating OPSGenerator')

    def makeDocument(self, titlestring):
        """
        This method may be used to create a new document for writing as xml
        to the OPS subdirectory of the ePub structure.
        """
        impl = xml.dom.minidom.getDOMImplementation()
        doctype = impl.createDocumentType('html',
                                          '-//W3C//DTD XHTML 1.1//EN'
                                          'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd')
        doc = impl.createDocument(None, 'html', doctype)
        root = doc.lastChild
        root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
        root.setAttribute('xml:lang', 'en-US')
        head = doc.createElement('head')
        title = doc.createElement('title')
        title.appendChild(doc.createTextNode(titlestring))
        link = doc.createElement('link')
        link.setAttribute('rel', 'stylesheet')
        link.setAttribute('href', 'css/article.css')
        link.setAttribute('type', 'text/css')
        meta = doc.createElement('meta')
        meta.setAttribute('http-equiv', 'Content-Type')
        meta.setAttribute('content', 'application/xhtml+xml')
        headlist = [title, link, meta]
        for tag in headlist:
            head.appendChild(tag)
        root.appendChild(head)
        body = doc.createElement('body')
        root.appendChild(body)
        return doc

    def writeDocument(self, name, document):
        """
        This function will write an DOM document to an XML file.
        """
        with open(name, 'wb') as out:
            out.write(document.toprettyxml(encoding='utf-8'))

    def expungeAttributes(self, node):
        """
        This method will remove all attributes of a any provided node.
        """
        while node.attributes.length:
            node.removeAttribute(node.attributes.item(0).name)
