# -*- coding: utf-8 -*-
"""
openaccess_epub.quickstart

Used for configuring an installation of OpenAccess_EPUB
"""

from openaccess_epub.utils import cache_location
import os

LOCAL_DIR = os.get_cwd()
CACHE_LOCATION = cache_location()

CONFIG_TEXT='''/
# -*- coding: utf-8 -*-
#
# OpenAccess_EPUB configuration file, created by oae-quickstart on
# {now}. The script detected OpenAccess_EPUB v.{version} at that time.
#
# At this point in time, all possible values for configuration are represented
# in this file. Suggested defaults exist for all values, but each may receive
# alternatives from the user. To reconfigure or reset to defaults, simply run
# oae-quickstart again.
#
# Please note that some of the configurations in this file may be overridden by
# flags passed manually to the oaepub script.

import os.path
import sys
import logging

# oaepub needs to be able to reliably find this config file; it will always be
# located in the directory returned by openaccess_epub.utils.cache_location().
# This directory is:  (path string)

cache_location = '{cache-location}'

# -- General Caching Configuration --------------------------------------------

# Image caching is helpful mostly for developers without local access to images
# which go into ePubs, this allows one to avoid re-downloading images during
# testing. Use image caching? (boolean)

image_caching = {image_caching}

# Where should the image cache be located? Use an absolute path. (path string)

image_cache = '{image_cache}'

# Log caching is helpful mostly for reporting errors that may be found some
# time after content creation and the original log may be missing. This option
# may be uncommon, and it defaults to False (boolean).

log_caching = {log_caching}

# Where should the log cache be located? Use an absolute path. (path string)

log_cache = '{log_cache}'

# Unless OpenAccess_EPUB is able to locate a local CSS file for inclusion in
# the ePub output, it will attempt to 
'''

