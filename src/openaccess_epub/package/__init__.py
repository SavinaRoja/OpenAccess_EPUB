# -*- coding: utf-8 -*-

"""
openaccess_epub.package provides facilities for producing EPUB package
documents

The Package Document carries bibliographic and structural metadata about an EPUB
Publication, and is thus the primary source of information about how to process
and display it. It is a part of both the EPUB 2 and EPUB 3 specifications and is
the point of processing which tells reading systems which version of EPUB the
document represents.
"""

#This module will be superceding the previouse opf module. It will become more
#general and capable of producing package info for EPUB2, and EPUB3.

#Standard Library modules
import logging

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__

log = logging.getLogger('openaccess_epub.package')


class Package(object):
    """
    The Package class
    """

    def __init__(self, collection=False):
        self.collection = collection

