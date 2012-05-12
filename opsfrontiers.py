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
        #From "10.3389/fimmu.2012.00104" get "fimmu.2012.00104"
        self.doi_frag = self.doi.split('10.3389/')[1]
        self.makeFragmentIdentifiers()
        self.ops_dir = os.path.join(output_dir, 'OPS')

    def createSynopsis(self):
        """
        This method encapsulates the functions necessary to create the synopsis
        segment of the article.
        """
        pass

    def createMain(self):
        """
        This method encapsulates the functions necessary to create the main
        segment of the article.
        """
        pass

    def createBiblio(self):
        """
        This method encapsulates the functions necessary to create the biblio
        segment of the article.
        """
        pass

    def createTables(self):
        """
        This method encapsulates the functions necessary to create a file
        containing html versions of all the tables in the article. If there
        are no tables, the file is not created.
        """
        pass

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
        print('Initiating OPSFrontiers')

import article

mydoc = article.Article('downloaded_xml_files/fimmu-03-00104.xml')
myops = OPSFrontiers(mydoc, os.path.join('output', 'fimmu-03-00104'))
print(myops.doi)

