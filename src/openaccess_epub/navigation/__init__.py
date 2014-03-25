# -*- coding: utf-8 -*-

"""
openaccess_epub.navigation provides facilities for producing EPUB navigation
documents

The Navigation Document is a required component of an EPUB document in both
EPUB2 and EPUB3. OpenAccess_EPUB provides support for both EPUB versions with
this module. The Navigation class can work with either a single article or with
multiple articles. The processing of articles for important navigation mapping
is currently publisher agnostic, however since this document is also used for
specifying metadata regarding the entire EPUB document (and this metadata may be
represented differently for each publisher), the details of the metadata
parsing for the article will be dependent on its publisher.
"""

#This module will be superceding the previouse ncx module. It will become more
#general and capable of producing navigation for EPUB2, and EPUB3.

#Standard Library modules
import logging

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules


log = logging.getLogger('openaccess_epub.navigation')


class Navigation(object):

    def __init__(self, collection=False):
        self.collection = collection