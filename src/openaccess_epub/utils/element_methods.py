# -*- coding: utf-8 -*-
"""
This module defines a set of methods for XML document parsing and manipulation
patterns beyond those which are provided by xml.dom.minidom.

Incorporating these methods into the module provides a single definition point
for the method that may be utilized in different sections.
"""

import xml.dom.minidom as minidom
import xml.parsers.expat
import html.parser
import logging

log = logging.getLogger('openaccess_epub.utils.element_methods')

def get_children_by_tag_name(tagname, node):
    """
    Search for all direct children with a particular element type name.

    This method is similar to getElementsByTagName except it does not search
    any deeper than the immediate children. It returns a list with 0 or more
    nodes.
    """
    child_list = []
    for child in node.childNodes:
        try:
            tag = child.tagName
        #Some nodes (text and comments) have no tagName
        except AttributeError:
            pass
        else:
            if tag == tagname:
                child_list.append(child)
    return child_list

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


def remove_all_attributes(node):
    """
    This method will remove all attributes of any provided element.
    """
    while node.attributes.length:
        node.removeAttribute(node.attributes.item(0).name)


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

