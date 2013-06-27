# -*- coding: utf-8 -*-
"""
This module defines a set of methods for XML document parsing and manipulation
patterns beyond those which are provided by xml.dom.minidom.

Incorporating these methods into the module provides a single definition point
for the method that may be utilized in different sections.
"""

from lxml import etree
from copy import deepcopy
import xml.dom.minidom as minidom
import xml.parsers.expat
import html.parser
import logging

log = logging.getLogger('openaccess_epub.utils.element_methods')

def append_new_text(destination, text, join_str=None):
    """
    This method provides the functionality of adding text appropriately
    underneath the destination node. This will be either to the destination's
    text attribute or to the tail attribute of the last child.
    """
    if join_str is None:
        join_str = ' '
    if len(destination) > 0:  # Destination has children
        last = destination[-1]
        if last.tail is None:  # Last child has no tail
            last.tail = text
        else:  # Last child has a tail
            last.tail = join_str.join([last.tail, text])
    else:  # Destination has no children
        if destination.text is None:  # Destination has no text
            destination.text = text
        else:  # Destination has a text
            destination.text = join_str.join([destination.text, text])

def append_all_below(destination, source, join_str=None):
    """
    Compared to xml.dom.minidom, lxml's treatment of text as .text and .tail
    attributes of elements is an oddity. It can even be a little frustrating
    when one is attempting to copy everything underneath some element to
    another element; one has to write in extra code to handle the text. This
    method provides the functionality of adding everything underneath the
    source element, in preserved order, to the destination element.
    """
    if join_str is None:
        join_str = ' '
    if source.text is not None:  # If source has text
        if len(destination) == 0:  # Destination has no children
            if destination.text is None:  # Destination has no text
                destination.text = source.text
            else:  # Destination has a text
                destination.text = join_str.join([destination.text, source.text])
        else:  # Destination has children
            #Select last child
            last = destination[-1]
            if last.tail is None:  # Last child has no tail
                last.tail = source.text
            else:  # Last child has a tail
                last.tail = join_str.join([last.tail, source.text])
    for each_child in source:
        destination.append(deepcopy(each_child))

def all_text(element):
    """
    A method for extending lxml's functionality, this will find and concatenate
    all text data that exists one level immediately underneath the given
    element. Unlike etree.tostring(element, method='text'), this will not 
    recursively walk the entire underlying tree. It merely combines the element
    text attribute with the tail attribute of each child.
    """
    if element.text is None:
        text = []
    else:
        text = [element.text]
    tails = [child.tail for child in element if child.tail is not None]
    tails = [tail.strip() for tail in tails if tail.strip()]
    return ' '.join(text + tails)

def remove_all_attributes(element, exclude=None):
    """
    This method will remove all attributes of any provided element.

    A list of strings may be passed to the keyward-argument "exclude", which
    will serve as a list of attributes which will not be removed.
    """
    if exclude is None:
        exclude = []
    for k in element.attrib.keys():
        if k not in exclude:
            element.attrib.pop(k)

def get_attribute(element, attribute):
    """
    With lxml's built in methods, if you attempt to access an attribute
    that does not exist, you will get a KeyError. To deal with attributes
    that are optional, you would have to follow one of these patterns:

      try:
        optional_attr = some_element.attrib['optional']
      except KeyError:
        optional_attr = None
      if optional_attr:  # Or this could be an else clause
        do_stuff

      if 'optional' in some_element.attrib:
        optional_attr = some_element.attrib['optional']
      else:
        optional_attr = None
      if optional_attr:
        do_stuff

    Doing this for such a common job may be an annoyance, so this method
    encapsulates the first pattern above to make things cleaner. The new
    pattern, using this method, is:

      optional_attr = get_attribute(some_element, 'optional')
      if optional_attr:
        do_stuff
    """
    try:
        optional_attribute = element.attrib[attribute]
    except KeyError:
        return None
    else:
        return optional_attribute

def ns_format(element, namespaced_string):
    """
    Provides a convenient method for adapting a tag or attribute name to
    use lxml's format. Use this for tags like ops:switch or attributes like
    xlink:href.
    """
    if ':' not in namespaced_string:
        print('This name contains no namespace, returning it unmodified: ' + namespaced_string)
        return namespaced_string
    namespace, name = namespaced_string.split(':')
    return '{' + element.nsmap[namespace] + '}' + name

def rename_attributes(element, attrs):
    """
    Renames the attributes of the element. Accepts the element and a dictionary
    of string values. The keys are the original names, and their values will be
    the altered names. This method treats all attributes as optional and will
    not fail on missing attributes.
    """
    for name in attrs.keys():
        if name not in element.attrib:
            continue
        else:
            element.attrib[attrs[name]] = element.attrib.pop(name)


def elevate_element(node, adopt_name=None, adopt_attrs=None):
        """
        This method serves a specialized function. It comes up most often when
        working with block level elements that may not be contained within
        paragraph elements, which are presented in the source document as
        inline elements (inside a paragraph element).

        It would be inappropriate to merely insert the block element at the
        level of the parent, since this disorders the document by placing
        the child out of place with its siblings. So this method will elevate
        the node to the parent level and also create a new parent to adopt all
        of the siblings after the elevated child.

        The adopting parent node will have identical attributes and tag name
        as the original parent unless specified otherwise.
        """

        #These must be collected before modifying the xml
        parent = node.getparent()
        grandparent = parent.getparent()
        child_index = parent.index(node)
        parent_index = grandparent.index(parent)
        #Get a list of the siblings
        siblings = list(parent)[child_index+1:]
        #Insert the node after the parent
        grandparent.insert(parent_index+1, node)
        #Only create the adoptive parent if there are siblings
        if len(siblings) > 0 or node.tail is not None:
            #Create the adoptive parent
            if adopt_name is None:
                adopt = etree.Element(parent.tag)
            else:
                adopt = etree.Element(adopt_name)
            if adopt_attrs is None:
                for key in parent.attrib.keys():
                    adopt.attrib[key] = parent.attrib[key]
            else:
                for key in adopt_attrs.keys():
                    adopt.attrib[key] = adopt_attrs[key]
            #Insert the adoptive parent after the elevated child
            grandparent.insert(grandparent.index(node)+1, adopt)
        #Transfer the siblings to the adoptive parent
        for sibling in siblings:
            adopt.append(sibling)
        #lxml's element.tail attribute presents a slight problem, requiring the
        #following oddity
        #Set the adoptive parent's text to the node.tail
        if node.tail is not None:
            adopt.text = node.tail
            node.tail = None  # Remove the tail


def remove(node):
    """
    A simple way to remove an element node from its tree.
    """
    parent = node.getparent()
    parent.remove(node)


def replace(old, new):
    """
    A simple way to replace one element node with another.
    """
    parent  = old.getparent()
    parent.replace(old, new)


def insert_before(old, new):
    """
    A simple way to insert a new element node before the old element node among
    its siblings.
    """
    parent = old.getparent()
    parent.insert(parent.index(old), new)


def comment(node):
    """
    Converts the node received to a comment, in place, and will also return the
    comment element.
    """
    parent = node.parentNode
    comment = node.ownerDocument.createComment(node.toxml())
    parent.replaceChild(comment, node)
    return comment


def uncomment(comment):
    """
    Converts the comment node received to a non-commented element, in place,
    and will return the new node.

    This may fail, primarily due to special characters within the comment that
    the xml parser is unable to handle. If it fails, this method will log an
    error and return None
    """
    parent = comment.parentNode
    h = html.parser.HTMLParser()
    data = h.unescape(comment.data)
    try:
        node = minidom.parseString(data).firstChild
    except xml.parsers.expat.ExpatError:  # Could not parse!
        log.error('Could not uncomment node due to parsing error!')
        return None
    else:
        parent.replaceChild(node, comment)
        return node

