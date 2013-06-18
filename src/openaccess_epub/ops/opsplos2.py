# -*- coding: utf-8 -*-
"""
This module defines an OPS content generator class for PLoS. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
from .opsmeta import OPSMeta
from lxml import etree
from copy import deepcopy
import os.path
import logging

log = logging.getLogger('OPSPLoS')


class OPSPLoS(OPSMeta):
    """
    This provides the full feature set to create OPS content for an ePub file
    from a PLoS journal article.
    """
    def __init__(self, article, output_dir):
        OPSMeta.__init__(self, article)
        main = self.make_document('main')
        if article.body is not None:
            print('copying!')
            body_copy = deepcopy(article.body)
            main.getroot().append(body_copy)
            for i in main.getroot():
                print(i)
        self.write_document('content.xml', main)
    