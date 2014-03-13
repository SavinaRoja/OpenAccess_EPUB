# -*- coding: utf-8 -*-
"""
openaccess_epub is the root package for OpenAccess_EPUB

The openaccess_epub package contains all of the packages and sub-modules for the
OpenAccess_EPUB project, which provides tools for processing academic journal
articles in the Journal Publishing Tag Set XML format as well as generating
EPUB documents from the processed information. XML parsing and editing is
performed using lxml.
"""

import os

from logging import getLogger

log = getLogger('openaccess_epub')

#Add references to data files
_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'data', path)

JPTS10_PATH = get_data('dtds/jpts10/journalpublishing.dtd')
JPTS11_PATH = get_data('dtds/jpts11/journalpublishing.dtd')
JPTS20_PATH = get_data('dtds/jpts20/journalpublishing.dtd')
JPTS21_PATH = get_data('dtds/jpts21/journalpublishing.dtd')
JPTS22_PATH = get_data('dtds/jpts22/journalpublishing.dtd')
JPTS23_PATH = get_data('dtds/jpts23/journalpublishing.dtd')
JPTS30_PATH = get_data('dtds/jpts30/journalpublishing3.dtd')

from ._version import __version__
