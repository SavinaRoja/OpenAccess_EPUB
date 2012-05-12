"""
This module defines an OPS content generator class for Frontiers. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import opsgenerator
import os
import os.path
import logging


class OPSFrontiers(opsgenerator.OPSGenerator):
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
        This will create useful fragment identifier strings.
        """
        #Frontiers formats its DOIs like "10.3389/fimmu.2012.00104"
        #I want the part that conveys journal and article, "fimmu.2012.00104"
        aid = self.doi.split('10.3389/')[1]
        self.synop_frag = 'synop.{0}.xml'.format(aid) + '#{0}'
        self.main_frag = 'main.{0}.xml'.format(aid) + '#{0}'
        self.biblio_frag = 'biblio.{0}.xml'.format(aid) + '#{0}'
        self.tables_frag = 'tables.{0}.xml'.format(aid) + '#{0}'

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSFrontiers')

import article

mydoc = article.Article('downloaded_xml_files/fimmu-03-00104.xml')
myops = OPSFrontiers(mydoc, 'test_output')
print(myops.doi)

