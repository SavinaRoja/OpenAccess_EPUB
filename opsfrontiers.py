"""
This module defines an OPS content generator class for Frontiers. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import opsgenerator
import os
import os.path
import logging
import utils


class InputError(Exception):
    """
    This is a custom exception for unexpected input from a publisher.
    """
    def __init__(self, detail):
        self.detail = detail

    def __str__(self):
        return self.detail


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

        #Create the title for the article
        title = self.appendNewElement('h1', body)
        self.setSomeAttributes(title, {'id': 'title',
                                       'class': 'article-title'})
        title.childNodes = self.metadata.title.article_title.childNodes

        #Get authors
        auths = []
        for contrib in self.metadata.contrib:
            if contrib.attrs['contrib-type'] == 'author':
                auths.append(contrib)
            else:
                if not contrib.attrs['contrib-type']:
                    print('No contrib-type provided for contibutor!')
                else:
                    print('Unexpected value for contrib-type')

        #Parse authors into formatted xml
        auth_el = self.appendNewElement('h3', body)
        first = True
        for auth in auths:
            if not first:
                self.appendNewText(', ', auth_el)
            else:
                first = False
            if not auth.anonymous:
                given = auth.name[0].given
                surname = auth.name[0].surname
                name = given + ' ' + surname
            else:
                name = 'Anonymous'
            self.appendNewText(name, auth_el)
            for x in auth.xref:
                s = x.node.getElementsByTagName('sup')
                if s:
                    s = utils.nodeText(s[0])
                else:
                    s = u'!'
                _sup = self.appendNewElement('sup', auth_el)
                _a = self.appendNewElement('a', _sup)
                _a.setAttribute('href', self.synop_frag.format(x.rid))
                self.appendNewText(s, _a)

        #Create the affiliations text
        for aff in self.metadata.affs:
            affp = self.appendNewElement('p', body)
            #Frontiers appears to include the following
            #<sup>, <institution>, and <country>
            try:
                sup = aff.getElementsByTagName('sup')[0]
            except IndexError:
                aff_id = aff.getAttribute('id')
                try:
                    sup_text = aff_id.split('aff')[1]
                except IndexError:
                    raise InputError('Could not identify affiliation number!')
            else:
                sup_text = utils.nodeText(sup)
            affp.setAttribute('id', aff.getAttribute('id'))
            aff_sup = self.appendNewElement('sup', affp)
            self.appendNewText(sup_text, aff_sup)
            #These will be considered optional
            try:
                inst = aff.getElementsByTagName('institution')[0]
            except IndexError:
                pass
            else:
                inst = utils.nodeText(inst)
                self.appendNewText(inst, affp)
            try:
                ctry = aff.getElementsByTagName('country')[0]
            except IndexError:
                pass
            else:
                ctry = utils.nodeText(ctry)
                self.appendNewText(', ' + ctry, affp)

        #To the best of my knowledge, Frontiers only has one kind of abstract
        for abstract in self.metadata.abstract:
            if abstract.type:
                print('abstract-type specified!: {0}'.format(abstract.type))
            body.appendChild(abstract.node)
            abstract.node.tagName = 'div'
            abstract.node.setAttribute('id', 'abstract')
            self.expungeAttributes(abstract.node)

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.synop_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def createMain(self):
        """
        This method encapsulates the functions necessary to create the main
        segment of the article.
        """

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.main_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def createBiblio(self):
        """
        This method encapsulates the functions necessary to create the biblio
        segment of the article.
        """

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.bib_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

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
        self.bib_frag = 'biblio.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.tables_frag = 'tables.{0}.xml'.format(self.doi_frag) + '#{0}'

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSFrontiers')
