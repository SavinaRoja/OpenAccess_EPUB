# -*- coding: utf-8 -*-
"""
This module provides the basic tools necessary to create the NCX (Navigation
Center eXtended) file for ePub. The specification for this file is a subsection
of the OPF specification. See:

http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.4.1
http://www.niso.org/workrooms/daisy/Z39-86-2005.html#NCX

The NCX file is REQUIRED for valid ePub, but readers support it OPTIONALLY. Its
job is to provide a more advanced Table of Contents-style navigation system for
the ePub beyond what is done in the OPF file.
"""

import openaccess_epub.utils as utils
import os
import xml.dom.minidom
import logging

log = logging.getLogger('NCX')

class NCX(object):
    """
    This class represents the NCX file, its generation with input, and its
    output rendering.

    The NCX serves to provide additional Table of Contents-style navigation
    through the ePub file.

    When the NCX class initiates, it contains no content, creating only the
    basic file framework and static data. To pass input articles to the NCX
    class, whether for Single Input Mode or for Collection Mode, use the
    OPF.take_article method.

    Similar to the opf.OPF class, the NCX class maintains a notion of internal
    state. This gives it focus on a single input article at a time,
    incorporating what it needs from the content data to generate internal data
    structures. This model serves as a framework that makes Collection Mode
    much easier and makes cross-journal support possible; it makes little
    difference to Single Input unless one is using an unusual workflow (such as
    using the same NCX instance to generate .ncx files for different ePubs).
    """
    def __init__(self):
        pass
