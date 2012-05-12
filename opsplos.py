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
    from a PLoS journal article.
    """
    def __init__(self, article, output_dir):
        opsgenerator.OPSGenerator.__init__(self)
        print('Generating OPS content...')
        self.metadata = article.metadata
        self.doi = article.getDOI()
        #From "10.1371/journal.pone.0035956" get "pone.0335956"
        self.doi_frag = self.doi.split('journal.')[1]
        self.makeFragmentIdentifiers()
        self.ops_dir = os.path.join(output_dir, 'OPS')

    def makeFragmentIdentifiers(self):
        """
        This will create useful fragment identifier strings.
        """
        self.synop_frag = 'synop.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.main_frag = 'main.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.biblio_frag = 'biblio.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.tables_frag = 'tables.{0}.xml'.format(self.doi_frag) + '#{0}'

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSPLoS')


import article

mydoc = article.Article('downloaded_xml_files/journal.pone.0035956.xml')
myops = OPSPLoS(mydoc, os.path.join('output', 'journal.pone.0035956'))
print(myops.doi)

