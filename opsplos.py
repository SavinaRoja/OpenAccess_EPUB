"""
This module defines an OPS content generator class for PLoS. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import opsgenerator
import os
import os.path
import logging

class OPSPLoS(opsgenerator.OPSGenerator):
    """
    This provides the full feature set to create OPS content for an ePub file
    from a Frontiers journal article.
    """
    def __init__(self, article, output_dir):
        opsgenerator.OPSGenerator.__init__(self)
        print('Generating OPS content...')
        self.metadata = article.metadata
        self.doi = article.getDOI()
        self.makeFragmentIdentifiers()

    def makeFragmentIdentifiers(self):
        """
        This will create useful fragement identifier strings.
        """
        #PLoS formats its DOIs like "10.1371/journal.pone.0035956"
        #I want the part that conveys journal and article, "pone.0335956"
        aid = self.doi.split('journal.')[1]
        self.synop_frag = 'synop.{0}.xml'.format(aid) + '#{0}'
        self.main_frag = 'main.{0}.xml'.format(aid) + '#{0}'
        self.biblio_frag = 'biblio.{0}.xml'.format(aid) + '#{0}'
        self.tables_frag = 'tables.{0}.xml'.format(aid) + '#{0}'

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSPLoS')


import article

mydoc = article.Article('downloaded_xml_files/journal.pone.0035956.xml')
myops = OPSPLoS(mydoc, 'test_output')
print(myops.doi)
