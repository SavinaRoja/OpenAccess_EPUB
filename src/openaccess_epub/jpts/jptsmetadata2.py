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
    A union of metadata elements will be represented by it.
    """
    def __init__(self, document):
        self.dtd_version = self.dtd_version()  # A string for DTD version
        self.document = document  # The minidom document element for article
        self.get_top_level_elements()

    def get_top_level_elements(self):
        """
        The 
        """

    
    def dtd_version(self):
        return ''