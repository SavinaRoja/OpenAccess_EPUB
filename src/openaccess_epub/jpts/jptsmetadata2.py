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


class JPTSInputError(Exception):
    pass


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
        self.journal_meta = self.front.getElementsByTagName('journal-meta')[0]
        #The <article-meta> element is required
        self.article_meta = self.front.getElementsByTagName('article-meta')[0]
        #The <notes> element is 0 or 1; if not found, self.notes will be None
        self.notes = element_methods.getOptionalChild('notes', self.front)

    def parse_metadata(self):
        """
        The master function for parsing metadata; do not override.
        """
        self.parse_intersecting_metadata()
        self.parse_unique_metadata()

    def parse_intersecting_metadata(self):
        """
        Parses the metadata features present (in identical form) in all DTD
        versions; do not override this method.

        Acts on the elements contained in the <front> and <back> elements of
        the article.
        """
        ### front ###
        ###   journal-meta ###
        #journal_id is a dictionary, keyed by journal-id-type
        self.journal_id = self.extract_journal_id()
        #journal_
        ###   article-meta ###

    def parse_unique_metadata(self):
        """
        Parses the metadata features unique to the DTD version. This is a dummy
        function in this base class; override this method in the inheritors.

        Acts on the unique elements contained in <front> and <back> elements,
        as well as <floats-wrap> or <floats-group>, depending on version.
        """
        pass

    def extract_journal_id(self):
        """
        <journal-id> is a required, one or more, sub-element of <journal-meta>.
        It can only contain text, numbers, or special characters. It has a
        single potential attribute, 'journal-id-type', whose value is used as a
        key to access the text data of its tag.

        This should return a dictionary with at least one element with the
        following form : {journal-id-type: unicode-text}
        """
        journal_ids = {}
        for journal_id in self.journal_meta.getElementsByTagName('journal-id'):
            text = element_methods.node_text(journal_id)
            type = journal_id.getAttribute('journal-id-type')
            journal_ids[type] = text
        if not journal_ids:
            raise JPTSInputError('Missing mandatory journal-id')
        return journal_id

    def dtd_version(self):
        return ''


class JPTSMetadata20(JPTSMetadata):
    """
    This class provides metadata support for articles published according to
    the Journal Publishing Tag Set version 2.0
    """

    def dtd_version(self):
        return '2.0'

class JPTSMetadata21(JPTSMetadata):
    """
    This class provides metadata support for articles published according to
    the Journal Publishing Tag Set version 2.1
    """

    def dtd_version(self):
        return '2.1'

class JPTSMetadata22(JPTSMetadata):
    """
    This class provides metadata support for articles published according to
    the Journal Publishing Tag Set version 2.2
    """

    def dtd_version(self):
        return '2.2'

class JPTSMetadata23(JPTSMetadata):
    """
    This class provides metadata support for articles published according to
    the Journal Publishing Tag Set version 2.3
    """

    def dtd_version(self):
        return '2.3'

class JPTSMetadata30(JPTSMetadata):
    """
    This class provides metadata support for articles published according to
    the Journal Publishing Tag Set version 3.0
    """

    def dtd_version(self):
        return '3.0'
