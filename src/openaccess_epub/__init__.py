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


def get_data_path(path):
    """
    Renders an absolute path to the specified path in the data section.

    This function is used primarily by openaccess_epub.article.Article, to
    successfully access and the .dtd files. These files should be located in the
    'data' directory and this placed within the openaccess_epub package
    directory. This function renders an absolute path (OS-appropriate) that is
    the join of the package directory, 'data', and the specified `path`
    argument.

    Parameters
    ----------
    path : str
        A path within the data directory.

    Returns
    -------
    path : str
        A string for the absolute path to the data.
    """
    return os.path.join(_ROOT, 'data', path)

JPTS10_PATH = get_data_path('dtds/jpts10/journalpublishing.dtd')
JPTS11_PATH = get_data_path('dtds/jpts11/journalpublishing.dtd')
JPTS20_PATH = get_data_path('dtds/jpts20/journalpublishing.dtd')
JPTS21_PATH = get_data_path('dtds/jpts21/journalpublishing.dtd')
JPTS22_PATH = get_data_path('dtds/jpts22/journalpublishing.dtd')
JPTS23_PATH = get_data_path('dtds/jpts23/journalpublishing.dtd')
JPTS30_PATH = get_data_path('dtds/jpts30/journalpublishing3.dtd')

from ._version import __version__
