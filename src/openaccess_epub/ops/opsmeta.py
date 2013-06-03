# -*- coding: utf-8 -*-
"""
This module defines a base class for the generation of Open Publication
Structure content. These tools facilitate the creation of OPS documents
independent of tag set version or publisher. This class is not a full-featured
translator from any XML format to OPS XML for ePub; derived classes for each
tag set and/or publisher must provide these functions.
"""

import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
import xml.dom.minidom
import logging

log = logging.getLogger('OPSMeta')


class OPSMeta(object):
    """
    This class provides several baseline features and functions required in
    order to produce OPS content.
    """
    def __init__(self):
        log.info('Initiating OPSMeta')
        self.document = self.make_document('base')

    def make_document(self, titlestring):
        """
        This method may be used to create a new document for writing as xml
        to the OPS subdirectory of the ePub structure.
        """
        impl = xml.dom.minidom.getDOMImplementation()
        doctype = impl.createDocumentType('html',
                                          '-//W3C//DTD XHTML 1.1//EN',
                                          'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd')
        doc = impl.createDocument(None, 'html', doctype)
        root = doc.lastChild
        root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
        root.setAttribute('xmlns:ops', 'http://www.idpf.org/2007/ops')
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

    def write_document(self, name, document):
        """
        This function will write a DOM document to an XML file.
        """
        with open(name, 'wb') as out:
            out.write(document.toprettyxml(encoding='utf-8'))

    def getSomeAttributes(self, element, names=[], remove=False):
        """
        This method accepts a list of strings corresponding to attribute names.
        It returns a dictionary of the form attributes[name] = value. If remove
        is set to True, it will delete the attributes after collection.
        """
        attrs = {}
        for name in names:
            attrs[name] = element.getAttribute('name')
            if remove:
                try:
                    element.removeAttribute(name)
                except xml.dom.NotFoundErr:
                    pass
        return attrs

    def setSomeAttributes(self, element, attrs={}):
        """
        This method accepts a dictionary of attribute{name:value} format to
        set an arbitrary number of attributes for an element.
        """
        for name in attrs:
            element.setAttribute(name, attrs[name])

    def removeSomeAttributes(self, element, names=[]):
        """
        This method will remove all attributes whose names are listed.
        """
        for name in names:
            element.removeAttribute(name)

    def renameAttributes(self, element, namepairs=[[]]):
        """
        This method accepts a two-dimensional list, tuple, or a combination
        thereof, where the second dimension consists of pairs of attribute
        names. The former attribute name will be replaced with the latter. For
        example, namepairs = [['monty', 'python], ['vanilla', 'fudge']] would
        change the names of the 'monty' and 'vanilla' attributes to 'python'
        and 'fudge'.respectively.
        """
        for ori, new in namepairs:
            val = element.getAttribute(ori)
            if val:
                element.removeAttribute(ori)
                element.setAttribute(new, val)

    def appendNewElement(self, newelement, parent):
        """
        A common idiom is to create an element and then immediately append it
        to another. This method allows that to be done more concisely. It
        returns the newly created and appended element.
        """
        new = self.document.createElement(newelement)
        parent.appendChild(new)
        return new

    def appendNewText(self, newtext, parent):
        """
        A common idiom is to create a new text node and then immediately append
        it to another element. This method makes that more concise. It does not
        return the newly created and appended text node
        """
        new = self.document.createTextNode(newtext)
        parent.appendChild(new)

    def appendNewElementWithText(self, newelement, newtext, parent):
        """
        A common xml editing idiom is to create a new element with some text in
        it and append it to pre-existing element. This method makes that more
        conscise. It will return the newly created element with the text added.
        """
        new = self.appendNewElement(newelement, parent)
        self.appendNewText(newtext, new)
        return new

    def convert_emphasis_elements(self, node):
        """
        The Journal Publishing Tag Set defines the following elements as
        emphasis elements: <bold>, <italic>, <monospace>, <overline>,
        <sans-serif>, <sc>, <strike>, <underline>. These need to be converted
        to appropriate OPS analogues. They have no defined attributes.

        Like other node handlers, this method requires a node or list of nodes
        to provide the scope of function, it will operate on all descendants
        of the passed node(s).
        """
        for b in node.getElementsByTagName('bold'):
            b.tagName = 'b'
        for i in node.getElementsByTagName('italic'):
            i.tagName = 'i'
        for m in node.getElementsByTagName('monospace'):
            m.tagName = 'span'
            m.setAttribute('style', 'font-family:monospace')
        for o in node.getElementsByTagName('overline'):
            o.tagName = 'span'
            o.setAttribute('style', 'text-decoration:overline')
        for s in node.getElementsByTagName('sans-serif'):
            s.tagName = 'span'
            s.setAttribute('style', 'font-family:sans-serif')
        for s in node.getElementsByTagName('sc'):
            s.tagName = 'span'
            s.setAttribute('style', 'font-variant:small-caps')
        for s in node.getElementsByTagName('strike'):
            s.tagName = 'span'
            s.setAttribute('style', 'text-decoration:line-through')
        for u in node.getElementsByTagName('underline'):
            u.tagName = 'span'
            u.setAttribute('style', 'text-decoration:underline')

    def convert_address_linking_elements(self, node):
        """
        The Journal Publishing Tag Set defines the following elements as
        address linking elements: <email>, <ext-link>, <uri>. The only
        appropriate hypertext element for linking in OPS is the <a> element.
        """
        #Convert email to a mailto link addressed to the text it contains
        for e in node.getElementsByTagName('email'):
            element_methods.remove_all_attributes(e)
            e.tagName = 'a'
            mailto = 'mailto:{0}'.format(utils.nodeText(e))
            e.setAttribute('href', mailto)
        #Ext-links often declare their address as xlink:href attribute
        #if that fails, direct the link to the contained text
        for e in node.getElementsByTagName('ext-link'):
            eid = e.getAttribute('id')
            e.tagName = 'a'
            xh = e.getAttribute('xlink:href')
            element_methods.remove_all_attributes(e)
            if xh:
                e.setAttribute('href', xh)
            else:
                e.setAttribute('href', utils.nodeText(e))
            if eid:
                e.setAttribute('id', eid)
        #Uris often declare their address as xlink:href attribute
        #if that fails, direct the link to the contained text
        for u in node.getElementsByTagName('uri'):
            u.tagName = 'a'
            xh = u.getAttribute('xlink:href')
            self.expungeAttributes(u)
            if xh:
                u.setAttribute('href', xh)
            else:
                u.setAttribute('href', utils.nodeText(u))
