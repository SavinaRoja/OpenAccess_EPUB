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
        self.createSynopsis()

    def createSynopsis(self):
        """
        This method encapsulates the functions necessary to create the synopsis
        segment of the article.
        """
        self.doc = self.makeDocument('synop')
        body = self.doc.getElementsByTagName('body')[0]
        title = self.appendNewElement('h1', body)
        self.setSomeAttributes(title, {'id': 'title',
                                       'class': 'article-title'})
        title.childNodes = self.metadata.title.article_title.childNodes
        auths = []
        for contrib in self.metadata.contrib:
            if contrib.attrs['contrib-type'] == 'author':
                auths.append(contrib)
            else:
                if not contrib.attrs['contrib-type']:
                    print('No contrib-type provided for contibutor!')
                else:
                    print('Unexpected value for contrib-type')
        #Create a <p> node to hold the affiliations text
        affp = self.appendNewElement('p', body)
        for aff in self.metadata.affs:
            #Frontiers appears to include the following
            #<sup>, <institution>. and <country>
            try:
                sup = aff.getElementsByTagName('sup')[0]
            except IndexError:
                aff_id = aff.getAttribute('id')
                try:
                    sup_text = aff_id.split('aff')[1]
                except IndexError:
                    raise InputError('Could not identify affiliation number!')
            else:
                
        #To the best of my knowledge, Frontiers only has one kind of abstract
        for abstract in self.metadata.abstract:
            if abstract.type:
                print('abstract-type specified!: {0}'.format(abstract.type))
            body.appendChild(abstract.node)
            abstract.node.tagName = 'div'
            abstract.node.setAttribute('id', 'abstract')
            self.expungeAttributes(abstract.node)
        #Finally, print this out or write to a document
        print(self.doc.toprettyxml(encoding='utf-8'))

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
