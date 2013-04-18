"""
This module defines methods intended to be used as an extended method set for
xml.dom.minidom classes.

These methods do not overwrite existing methods, so using them as monkey patch
extensions should not present a risk of unexpected behavior, these are merely
methods that I felt should be added to improve the readability and consistency
of the code base for OpenAccess_EPUB.

This methods in this module should be well documented to avoid confusion for
those referring back to the xml.dom documentation. The methods utilize
camelCase naming to emphasize their consistency with xml.dom, I am aware of the
conflict with PEP8.
"""


def getChildrenByTagName(self, tagName):
    """
    Search for all direct children with a particular element type name.

    This method is similar to getElementsByTagName except it does not search
    any deeper than the immediate children. It returns a list with 0 or more
    nodes.

    The only objects that should receive this method are Element and Document
    objects.
    """
    child_list = []
    for child in self.childNodes:
        try:
            tag = child.tagName
        #Some nodes (text and comments) have no tagName
        except AttributeError:
            pass
        else:
            if tag == tagName:
                child_list.append(child)
    return child_list


def removeAllAttributes(self):
    """
    This method will remove all attributes of any provided element.

    The only object that should receive this method is Element.
    """
    while self.attributes.length:
        self.removeAttribute(self.attributes.item(0).name)


def getAllAttributes(self, remove=False):
    """
    Returns a dictionary of all the attributes for an Element; takes the form
    of dict[attribute_name]=attribute_value.

    If the optional argument "remove" is set to True, this method will also
    remove all of the attributes from the element.

    The only object that should receive this method is Element.
    """
    attributes = {}
    keys = self.attributes.keys()
    for key in keys:
        attributes[key] = self.getAttribute(key)
    if remove:
        self.removeAllAttributes()
    return attributes


def elevateNode(self, adopt=''):
        """
        This method serves a specialized function. It will effectively elevate
        the level of a node by inserting it at the same level as its parent,
        immediately after the parent in the tree.
        
        
        There are some cases where a little surgery must take place in the
        manipulation of an XML document to produce valid ePub. This method
        covers the case where a node must be placed at the same level of its
        parent. All siblings that come after this node will be removed from
        the parent node as well, they will be added as children to a new parent
        node that will be of the same type as the first. For example:
        <p>Monty Python's <flying>Circus</flying> is <b>great</b>!</p>
        would be converted by elevateNode(flying_node) to:
        <p>Monty Python's </p><flying>Circus</flying><p> is <b>great</b>!</p>
        Take care when using this method and make sure it does what you want.
        """
        #These must be collected before modifying the xml
        parent = node.parentNode
        parent_sibling = parent.nextSibling
        grandparent = parent.parentNode
        node_index = parent.childNodes.index(node)
        #Now we make modifications
        grandparent.insertBefore(node, parent_sibling)
        if not adopt:
            adopt = parent.tagName
        adopt_element = self.doc.createElement(adopt)
        grandparent.insertBefore(adopt_element, parent_sibling)
        for child in parent.childNodes[node_index + 1:]:
            adopt_element.appendChild(child)


def removeSelf(self):
    """
    Removes the node from its parent. This is a convenience method which
    accesses the node's parentNode, then calls parent.removeChild() on itself.

    The Node Object should receive this method.
    """
    parent = self.parentNode
    parent.removeChild(self)


def replaceSelfWith(self, newChild):
    """
    Replace an existing node with a new node. This is a convenience method
    which accesses the node's parentNode, then calls parent.replaceChild()
    on the node with the newChild.

    The Node Object should receive this method.
    """
    parent = self.parentNode
    parent.replaceChild(newChild, self)
