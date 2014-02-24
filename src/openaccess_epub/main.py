# -*- coding: utf-8 -*-

"""
This is the main execution file for OpenAccess_EPUB. It provides the primary
mode of execution and interaction.
"""

#Standard Library Modules
import argparse
import sys
import os
import shutil
import logging
import traceback
import subprocess

#OpenAccess_EPUB Modules
from ._version import __version__
import openaccess_epub.utils as utils
import openaccess_epub.utils.input as u_input
from openaccess_epub.utils.images import get_images
import openaccess_epub.opf as opf
import openaccess_epub.ncx as ncx
import openaccess_epub.ops as ops
from openaccess_epub.article import Article

CACHE_LOCATION = utils.cache_location()
LOCAL_DIR = os.getcwd()

log = logging.getLogger('openaccess_epub.main')
