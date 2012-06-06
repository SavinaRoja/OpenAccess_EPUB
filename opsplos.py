"""
This module defines an OPS content generator class for PLoS. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import opsgenerator
import os
import os.path
import utils
import logging


class InputError(Exception):
    """
    This is a custom exception for unexpected input from a publisher.
    """
    def __init__(self, detail):
        self.detail = detail

    def __str__(self):
        return self.detail


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
        auths, edits = [], []
        for contrib in self.metadata.contrib:
            if contrib.attrs['contrib-type'] == 'author':
                auths.append(contrib)
            elif contrib.attrs['contrib-type'] == 'editor':
                edits.append(contrib)
            else:
                if not contrib.attrs['contrib-type']:
                    print('No contrib-type provided for contibutor!')
                else:
                    print('Unexpected value for contrib-type')
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

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.synop_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def createMain(self):
        """
        This method encapsulates the functions necessary to create the main
        segment of the article.
        """

        self.doc = self.makeDocument('main')
        body = self.doc.getElementsByTagName('body')[0]

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.main_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def createBiblio(self):
        """
        This method encapsulates the functions necessary to create the biblio
        segment of the article.
        """

        self.doc = self.makeDocument('biblio')
        body = self.doc.getElementsByTagName('body')[0]

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.bib_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def createTables(self):
        """
        This method encapsulates the functions necessary to create a file
        containing html versions of all the tables in the article. If there
        are no tables, the file is not created.
        """

        self.doc = self.makeDocument('tables')
        body = self.doc.getElementsByTagName('body')[0]

        with open(os.path.join(self.ops_dir, self.tab_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

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
        print('Initiating OPSPLoS')
