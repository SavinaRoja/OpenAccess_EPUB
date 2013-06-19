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
            last.tail = join_str.join(last.tail, text)
    else:  # Destination has no children
        if destination.text is None:  # Destination has no text
            destination.text = text
        else:  # Destination has a text
            destination.text = join_str.join(destination.text, text)

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
                destination.text = join_str.join(destination.text, source.text)
        else:  # Destination has children
            #Select last child
            last = destination[-1]
            if last.tail is None:  # Last child has no tail
                last.tail = source.text
            else:  # Last child has a tail
                last.tail = join_str.join(last.tail, source.text)
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
    tails = [child.tail.strip() for child in element if child.tail.strip()]
    return ' '.join(text + tails)

def remove_all_attributes(element):
    """
    This method will remove all attributes of any provided element.
    """
    for k in element.attrib.keys():
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
        optional_attr = some_element.attrib:['optional']
      else:
        optional_attr = None
      if optional_attr:
        do_stuff

    Doing this for such a common job is an annoyance, so this method
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

def get_optional_child(tagname, node, not_found=None):
    """
    This method is used to return the first child with the supplied tagName
    when the child may or may not exist.

    This saves some repetitive code during checks for child existence.
    """
    try:
        child = get_children_by_tag_name(tagname, node)[0]
    except IndexError:
        child = not_found
    return child

def get_all_attributes(node, remove=False):
    """
    Returns a dictionary of all the attributes for an Element; takes the form
    of dict[attribute_name]=attribute_value.

    If the optional argument "remove" is set to True, this method will also
    remove all of the attributes from the element.
    """
    attributes = {}
    keys = node.attributes.keys()
    for key in keys:
        attributes[key] = node.getAttribute(key)
    if remove:
        remove_all_attributes(node)
    return attributes


def elevate_node(node, adopt_name=''):
        """
        This method serves a specialized function. It will effectively elevate
        the level of a node by inserting it at the same level as its parent,
        immediately after the parent in the tree. All siblings of the node that
        came after the node in its original position will then be given to a
        new parent node placed immediately after the elevated node. By default,
        this new parent node will be the same as the original parent, but it
        may be altered using the adopt_name optional argument, string input will
        supply the new tagName.
        """
        #These must be collected before modifying the xml
        parent = node.parentNode
        parent_sibling = parent.nextSibling
        grandparent = parent.parentNode
        node_index = parent.childNodes.index(node)
        #Now we make modifications
        grandparent.insertBefore(node, parent_sibling)
        if not adopt_name:
            adopt_name = parent.tagName
        #ownerDocument is an undocumented attribute of Nodes, it gets the
        #Document object of which it is a part.
        adopt_element = node.ownerDocument.createElement(adopt_name)
        grandparent.insertBefore(adopt_element, parent_sibling)
        for child in parent.childNodes[node_index + 1:]:
            adopt_element.appendChild(child)


def remove(node):
    """
    Removes the node from its parent. This is a convenience method which
    accesses the node's parentNode, then calls parent.removeChild() on itself.
    """
    parent = node.parentNode
    parent.removeChild(node)


def replace_with(node, new_child):
    """
    Replace an existing node with a new node. This is a convenience method
    which accesses the node's parentNode, then calls parent.replaceChild()
    on the node with the newChild.
    """
    parent = node.parentNode
    parent.replaceChild(new_child, node)


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


def node_text(node):
    """
    This is to be used when a node may only contain text, numbers or special
    characters. This function will return the text contained in the node.
    Sometimes this text data contains spurious newlines and spaces due to
    parsing and original xml formatting. This function should strip such
    artifacts.
    """
    #Get data from first child of the node
    try:
        first_child_data = node.firstChild.data
    except AttributeError:  # Usually caused by an empty node
        return ''
    else:
        return '{0}'.format(first_child_data.strip())

