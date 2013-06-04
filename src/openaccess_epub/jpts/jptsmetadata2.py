# -*- coding: utf-8 -*-
"""
Most, if not all, Open Access journals appear to utilize the Journal Publishing
Tag Set as their archival and interchange data format for their articles.

This module provides classes for extracting the metadata contained within the
JPTS documents and representing them as python elements and data structures.

The different classes in this module correspond to different versions of the
JPTS and are strictly adherent to the DTD. Differences between journals, which
are sometimes based on subjective decisions, are not accounted for in these
metadata structures; instead these differences should be treated during later
processing as needed.

This module will seek to provide official support for the following JTPS DTD
versions: 2.0, 2.1, 2.2, 2.3, and 3.0
"""

from collections import namedtuple
from openaccess_epub.utils import OrderedSet
import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
import openaccess_epub.jpts.jptscontrib as jptscontrib
import logging


log = logging.getLogger('openaccess_epub.jpts.jptsmetadata')


class JPTSMetadata(object):
    """
    This class is the base class for the Journal Publishing Tag Set
    metadata. It defines the basic behavior of the version-specific JPTS
    metadata classes which inherit from it, and should not be used directly.
    An intersection of metadata elements will be represented by it.
    """
    def __init__(self, document):
        self.dtd_version = self.dtd_version()  # A string for DTD version
        self.document = document  # The minidom document element for article
        self.get_top_level_elements()
        self.get_front_child_elements()
        self.init_metadata()
        self.parse_metadata()

    def get_top_level_elements(self):
        """
        The various DTD versions define top level elements that occur under the
        document element, <article>.
        """
        #If any of the elements are not found, their value will be None
        #The <front> element is required, and singular
        self.front = self.document.getElementsByTagName('front')[0]
        #The <body> element is 0 or 1; it does not contain metadata
        self.body = element_methods.getOptionalChild('body', self.document)
        #The <back> element is 0 or 1
        self.back = element_methods.getOptionalChild('back', self.document)
        #The <floats-wrap> element is 0 or 1; relevant only to version 2.3
        self.floats_wrap = element_methods.getOptionalChild('floats-wrap', self.document)
        #The <floats-group> element is 0 or 1; relevant only to version 3.0
        self.floats_group = element_methods.getOptionaChild('floats-group', self.document)
        #The <sub-article> and <response> elements are defined in all supported
        #versions in the following manner: 0 or more, mutually exclusive
        self.sub_article = self.document.getElementsByTagName('sub-article')
        if self.sub_article:
            self.response = None
        else:
            self.sub_article = None
            self.response = self.document.getElementsByTagName('response')
            if not self.response:
                self.response = None

    def get_front_child_elements(self):
        """
        The various DTD versions all maintain the same definition of the
        elements that may be found directly beneath the <front> element.
        """
        #The <journal-meta> element is required
        self.journal_metadata = self.front.getElementsByTagName('journal-meta')[0]
        #The <article-meta> element is required
        self.article_metadata = self.front.getElementsByTagName('article-meta')[0]
        #The <notes> element is 0 or 1; if not found, self.notes will be None
        self.notes = element_methods.getOptionalChild('notes', self.front)

    def init_metadata(self):
        """
        The master function for initializing metadata; do not override.
        """
        self.init_intersecting_metadata()
        self.init_unique_metadata()

    def init_intersecting_metadata(self):
        """
        The intersection of metadata features (present in all DTD versions); do
        not override.
        """
        pass


    def init_unique_metadata(self):
        """
        The metadata features unique to the DTD version at hand; override this
        method.
        """
        pass

    def parse_metadata(self):
        """
        The master function for parsing metadata; do not override.
        """
        self.parse_journal_metadata()
        self.parse_article_metadata()
        self.parse_back_data()

    def parse_journal_metadata(self):
        """
        
        """
        pass

    def parse_article_metadata(self):
        """
        
        """
        pass

    def parse_back_metadata(self):
        """
        
        """
        pass

    def dtd_version(self):
        return ''