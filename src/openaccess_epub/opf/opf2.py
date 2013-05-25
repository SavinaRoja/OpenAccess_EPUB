# -*- coding: utf-8 -*-
"""
This module provides the basic tools necessary to create the Open Packaging
Format, OPF, file for OpenAccess_EPUB.

The OPF file has three basic jobs: it presents metadata about the file in the
Dublin Core prescribed vocabulary, it contains a manifest of all the files
within the ePub, and it provides a spine for a document-level read order.
This spine provides the read order that e-readers MUST support, while the NCX
provides a much finer-grained Table of Contents that e-readers SHOULD support.

The latter two of these jobs are likely to vary little in their action from
publisher to publisher, but care should be taken with the metadata parsing
from the input to output, as the publisher convention may differ and some of
the translation decisions are subjective.

Refer to the version of JPTS you are using and the jpts module, as well as the
Dublin Core specification and the dublincore module.
"""

import openaccess.utils as utils
import openaccess.dublincore as dublincore
import logging
import os
import time
import uuid
import xml.dom.minidom

log = logging.getLogger('OPF')


class OPF(oject):
    """
    This class represents the OPF file, its generation with input and how it
    renders to output.
    
    The OPF file handles three distinct tasks: Dublin Core Metadata about the
    ePub file, a file manifest the ePub, and a read-order spine for the ePub.
    
    When the OPF class initiates, it contains no content, creating only the
    basic file framework. To pass input articles to the OPF class, whether for
    Single Input Mode or for Collection Mode, use the OPF.take_article method.
    
    The OPF Class relies on a concept of internal state. This state represents
    the class' focus on a single article at a time. This is of little
    importance in Single Input mode, but is critical to Collection Mode.
    
    """
    def __init__(self, collection_mode):
        self.collection_mode = collection_mode

    def take_article(self, article):
        """
        Receives an instance of the Article class. This modifies the internal
        state of the OPF class to focus on the new article for the purposes of
        extracting metadata and content information.
        
        In Collection Mode, the addition of new articles to the OPF class
        results in cumulative (in order of receipt) content. In Single Input
        Mode, the addition of a new article will erase any information from the
        previous article.
        """
        pass

    def use_collection_mode(self):
        """Enables Collection Mode, sets self.collection_mode to True"""
        self.collection_mode = True

    def use_single_mode(self):
        """Disables Collection Mode, sets self.collection_mode to False"""
        self.collection_mode = False
        self.collection_mode = False