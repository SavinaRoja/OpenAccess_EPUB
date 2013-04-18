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
