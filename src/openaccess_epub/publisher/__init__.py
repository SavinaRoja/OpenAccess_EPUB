# -*- coding: utf-8 -*-

"""
openaccess_epub.publisher defines abstract publisher representation and content
conversion
"""

#Standard Library modules
import logging

#Non-Standard Library modules

#OpenAccess_EPUB modules

log = logging.getLogger('openaccess_epub.publisher')


class Publisher(object):
    """
    Meta class for publishers, sub-class per publisher to add support
    """
    def __init__(self):
        """
        The initialization of the Publisher class.
        """
        self.epub2_support = False
        self.epub3_support = False

    def pre_processing(self):
        """
        """
        pass

    def post_processing(self):
        """
        """
        pass
