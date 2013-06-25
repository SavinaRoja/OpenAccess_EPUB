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
from lxml import etree
import logging

log = logging.getLogger('OPSMeta')


class OPSMeta(object):
    """
    This class provides several baseline features and functions required in
    order to produce OPS content.
    """
    def __init__(self, article):
        if article.dtd_name == 'JPTS':
            self.convert_emphasis_elements = self.convert_JPTS_emphasis
        self.document = self.make_document('base')

    def make_document(self, titlestring):
        """
        This method may be used to create a new document for writing as xml
        to the OPS subdirectory of the ePub structure.
        """
        root = etree.XML('''<?xml version="1.0"?>\
<!DOCTYPE html  PUBLIC '-//W3C//DTD XHTML 1.1//EN'  'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'>\
<html xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml" xmlns:ops="http://www.idpf.org/2007/ops">\
</html>''')
        document = etree.ElementTree(root)
        html = document.getroot()
        head = etree.SubElement(html, 'head')
        title = etree.SubElement(head, 'title')
        title.text = titlestring
        link = etree.SubElement(head, 'link', attrib={'href': 'css/article.css',
                                                      'rel': 'stylesheet',
                                                      'type': 'text/css'})
        meta = etree.SubElement(head, 'meta', attrib={'content': 'application/xhtml+xml',
                                                      'http-equiv': 'Content-Type'})
        return document

    def write_document(self, name, document):
        """
        This function will write a document to an XML file.
        """
        with open(name, 'wb') as out:
            out.write(etree.tostring(document, encoding='utf-8'))

    def convert_JPTS_emphasis(self, element):
        """
        The Journal Publishing Tag Set defines the following elements as
        emphasis elements: <bold>, <italic>, <monospace>, <overline>,
        <sans-serif>, <sc>, <strike>, <underline>. These need to be converted
        to appropriate OPS analogues. They have no defined attributes.
        """
        for bold in element.findall('.//bold'):
            bold.tag = 'b'
        for italic in element.findall('.//italic'):
            italic.tag = 'i'
        for mono in element.findall('.//monospace'):
            mono.tag = 'span'
            mono.attrib['style'] = 'font-family:monospace'
        for over in element.findall('.//overline'):
            over.tag = 'span'
            over.attrib['style'] = 'text-decoration:overline'
        for sans in element.findall('.//sans-serif'):
            sans.tag = 'span'
            sans.attrib['style'] = 'font-family:sans-serif'
        for small in element.findall('.//sc'):
            small.tag = 'span'
            small.attrib['style'] = 'font-variant:small-caps'
        for strike in element.findall('.//strike'):
            strike.tag = 'span'
            strike.attrib['style'] = 'text-decoration:line-through'
        for under in element.findall('.//underline'):
            under.tag = 'span'
            under.attrib['style'] = 'text-decoration:underline'

    def convert_address_linking_elements(self, top):
        """
        The Journal Publishing Tag Set defines the following elements as
        address linking elements: <email>, <ext-link>, <uri>. The only
        appropriate hypertext element for linking in OPS is the <a> element.
        """
        #Convert email to a mailto link addressed to the text it contains
        for email in top.findall('.//email'):
            element_methods.remove_all_attributes(email)
            email.tag = 'a'
            email.attrib['href'] = 'mailto:{0}'.format(email.text)
        #Ext-links often declare their address as xlink:href attribute
        #if that fails, direct the link to the contained text
        for ext_link in top.findall('.//ext-link'):
            ext_link.tag = 'a'
            xlink_href_name = element_methods.ns_format(ext_link, 'xlink:href')
            xlink_href = element_methods.get_attribute(ext_link, xlink_href_name)
            element_methods.remove_all_attributes(ext_link, exclude=['id'])
            if xlink_href:
                ext_link.attrib['href'] = xlink_href
            else:
                ext_link.attrib['href'] = element_methods.all_text(ext_link)
        #Uris often declare their address as xlink:href attribute
        #if that fails, direct the link to the contained text
        for uri in top.findall('.//uri'):
            uri.tag = 'a'
            xlink_href_name = element_methods.ns_format(uri, 'xlink:href')
            xlink_href = element_methods.get_attribute(uri, xlink_href_name)
            element_methods.remove_all_attributes(uri)
            if xlink_href:
                uri.attrib['href'] = xlink_href
            else:
                uri.attrib['href'] = element_methods.all_text(uri)
