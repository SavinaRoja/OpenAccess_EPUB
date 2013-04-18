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