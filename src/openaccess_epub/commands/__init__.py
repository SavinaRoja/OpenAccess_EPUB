# -*- coding: utf-8 -*-

"""
openaccess_epub.commands defines modules useful as scripts, available through
oaepub interface.

The commands in the openaccess.commands module can be run as standalones or
through the `oaepub` interface installed with OpenAccess_EPUB. Each command's
interface is defined by its own documentation (using docopt). Some additional
documentation on the use of conversion commands is covered in
:ref:`conversion-overview`.
"""

from logging import getLogger

log = getLogger('openaccess_epub.commands')
