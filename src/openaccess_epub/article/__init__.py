# -*- coding: utf-8 -*-

"""
openaccess_epub.article  defines abstract article representation

The openaccess_epub.article contains the :class:`Article` class which is
instantiated per article XML file. Basic article structural elements are
collected and metadata is parsed according to DTD rules into a python data
structure. The Article class forms a basic unit in the procedure of analyzing
articles and in the conversion to EPUB.
"""

#Standard Library modules
import logging

#Non-Standard Library modules

#OpenAccess_EPUB modules
from openaccess_epub.article.article import Article

log = logging.getLogger('openaccess_epub.article')
