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
        self.html_tables = []
        self.createSynopsis()
        self.createMain()
        self.createBiblio()
        if self.html_tables:
            self.createTables()

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
                if x.ref_type == 'author-notes':
                    _sup = self.appendNewElement('sup', auth_el)
                    _a = self.appendNewElement('a', _sup)
                    _a.setAttribute('href', self.synop_frag.format(x.rid))
                    self.appendNewText(utils.nodeText(x.node), _a)
                elif x.ref_type == 'aff':
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

        #Refer to self.createArticleInfo()
        self.createArticleInfo(body)

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

    def createArticleInfo(self, body):
        """
        The 'article info' section is a segment of metadata information about
        the article that is of primary interest to human readers. This section
        is typically found after abstracts and summaries on a webpage, and at
        various locations on a PDF, though typically on the first page. For an
        ebook, this shall be presented similar to the webpage.
        """
        body.appendChild(self.doc.createElement('hr'))
        ainfo = self.appendNewElement('div', body)
        ainfo.setAttribute('id', 'articleInfo')
        if self.metadata.all_kwds:
            pk = self.appendNewElement('p', ainfo)
            bk = self.appendNewElement('b', pk)
            self.appendNewText('Keywords: ', bk)
            first = True
            for kwd in self.metadata.all_kwds:
                if first:
                    first = False
                else:
                    self.appendNewText(', ', pk)
                for cn in kwd.node.childNodes:
                    pk.appendChild(cn.cloneNode(True))
        pc = self.appendNewElement('p', ainfo)
        bc = self.appendNewElement('b', pc)
        self.appendNewText('Citation: ', bc)
        self.appendNewText('This feature not yet implemented!', pc)
        #Important dates might be publication dates or history dates
        pd = self.appendNewElement('p', ainfo)
        #For the publication dates
        pub_dates = self.metadata.pub_date
        try:
            epreprint = pub_dates['epreprint']
        except KeyError:
            epreprint = None
        try:
            epub = pub_dates['epub']
        except KeyError:
            epub = None
        #For the history dates
        history = self.metadata.history
        try:
            received = history['received']
        except KeyError:
            received = None
        try:
            accepted = history['accepted']
        except KeyError:
            accepted = None
        #Now that we collected the dates, let's use them:
        months = ['Offle', 'January', 'February', 'March', 'April',
                          'May', 'June', 'July', 'August', 'September',
                          'October', 'November', 'December']
        if received:
            bd = self.appendNewElement('b', pd)
            self.appendNewText('Received: ', bd)
            if received.day:
                self.appendNewText(received.day + ' ', pd)
            if received.month:
                m = int(received.month)
                self.appendNewText(months[m] + ' ', pd)
            self.appendNewText(received.year + '; ', pd)
        if epreprint:
            bd = self.appendNewElement('b', pd)
            self.appendNewText('Paper pending published: ', bd)
            if epreprint.day:
                self.appendNewText(epreprint.day + ' ', pd)
            if epreprint.month:
                m = int(epreprint.month)
                self.appendNewText(months[m] + ' ', pd)
            self.appendNewText(epreprint.year + '; ', pd)
        if accepted:
            bd = self.appendNewElement('b', pd)
            self.appendNewText('Accepted: ', bd)
            if accepted.day:
                self.appendNewText(accepted.day + ' ', pd)
            if accepted.month:
                m = int(accepted.month)
                self.appendNewText(months[m] + ' ', pd)
            self.appendNewText(accepted.year + '; ', pd)
        if epub:
            bd = self.appendNewElement('b', pd)
            self.appendNewText('Published online: ', bd)
            if epub.day:
                self.appendNewText(epub.day + ' ', pd)
            if epub.month:
                m = int(epub.month)
                self.appendNewText(months[m] + ' ', pd)
            self.appendNewText(epub.year + '; ', pd)
        pd.lastChild.data = pd.lastChild.data[:-2] + '.'
        #The declaration of the editor seems to be only in the author-notes
        author_notes = self.metadata.author_notes
        if author_notes:
            footnotes = author_notes.getElementsByTagName('fn')
            edit_by = None
            review_by = None
            corresp = []
            for fn in footnotes:
                if fn.getAttribute('fn-type') == 'edited-by':
                    p = fn.getElementsByTagName('p')[0]
                    if p.firstChild.data[:11] == 'Edited by: ':
                        edit_by = p.firstChild.data[11:]
                    elif p.firstChild.data[:13] == 'Reviewed by: ':
                        review_by = p.firstChild.data[13:]
                elif fn.getAttribute('fn-type') == 'corresp':
                    corresp.append(fn)
            if edit_by:
                pe = self.appendNewElement('p', ainfo)
                be = self.appendNewElement('b', pe)
                self.appendNewText('Edited by: ', be)
                self.appendNewText(edit_by, pe)
            if review_by:
                pr = self.appendNewElement('p', ainfo)
                br = self.appendNewElement('b', pr)
                self.appendNewText('Reviewed by: ', br)
                self.appendNewText(review_by, pr)
        #Print the copyright information
        perm = self.metadata.permissions
        pc = self.appendNewElement('p', ainfo)
        bc = self.appendNewElement('b', pc)
        self.appendNewText('Copyright: ', bc)
        self.appendNewText(utils.nodeText(perm.statement)[10:] + ' ', pc)
        l = perm.license
        for p in l.getElementsByTagName('p'):
            for cn in p.childNodes:
                pc.appendChild(cn.cloneNode(True))
        for uri in pc.getElementsByTagName('uri'):
            uri.tagName = 'a'
            self.renameAttributes(uri, [['xlink:href', 'href']])
        #Print the correspondence information
        for corr in corresp:
            pc = self.appendNewElement('p', ainfo)
            pc.setAttribute('id', corr.getAttribute('id'))
            bc = self.appendNewElement('b', pc)
            corr_p = corr.getElementsByTagName('p')[0]
            link_char = corr_p.firstChild.data[0]
            corr_p.firstChild.data = corr_p.firstChild.data[17:]
            for cn in corr_p.childNodes:
                pc.appendChild(cn.cloneNode(True))
            #The first character of the text in the <p> is the link char
            self.appendNewText(link_char + 'Correspondence: ', bc)
            for email in pc.getElementsByTagName('email'):
                email.tagName = 'a'
                mailto = 'mailto:{0}'.format(utils.nodeText(email))
                email.setAttribute('href', mailto)

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
