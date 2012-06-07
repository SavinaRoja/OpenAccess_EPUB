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
        self.article = article.root_tag
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
                if x.ref_type in ['author-notes', 'aff']:
                    try:
                        sup_el = x.node.getElementsByTagName('sup')[0]
                    except IndexError:
                        s = utils.nodeText(x.node)
                    else:
                        s = utils.nodeText(sup_el)
                    sup = self.appendNewElement('sup', auth_el)
                    _a = self.appendNewElement('a', sup)
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

        #Post processing node conversion
        self.convertEmphasisElements(body)
        self.convertAddressLinkingElements(body)

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
        #Here I make a complete copy of the article's body tag to the the main
        #document's DOM
        try:
            article_body = self.article.getElementsByTagName('body')[0]
        except IndexError:  # Article has no body...
            return None
        else:
            for item in article_body.childNodes:
                body.appendChild(item.cloneNode(deep=True))

        #Handle node conversion
        self.convertFigElements(body)
        self.convertTableWrapElements(body)
        self.convertEmphasisElements(body)
        self.convertAddressLinkingElements(body)
        self.convertXrefElements(body)

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
        are no tables, the file is not written.
        """

        self.doc = self.makeDocument('tables')
        body = self.doc.getElementsByTagName('body')[0]
        for table in self.html_tables:
            body.appendChild(table)

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
                    pk.appendChild(cn.cloneNode(deep=True))
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
                pc.appendChild(cn.cloneNode(deep=True))
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
                pc.appendChild(cn.cloneNode(deep=True))
            #The first character of the text in the <p> is the link char
            self.appendNewText(link_char + 'Correspondence: ', bc)
            for email in pc.getElementsByTagName('email'):
                email.tagName = 'a'
                mailto = 'mailto:{0}'.format(utils.nodeText(email))
                email.setAttribute('href', mailto)

    def convertAddressLinkingElements(self, node):
        """
        The Journal Publishing Tag Set defines the following elements as
        address linking elements: <email>, <ext-link>, <uri>. The only
        appropriate hypertext element for linking in OPS is the <a> element.
        """
        #Convert email to a mailto link addressed to the text it contains
        for e in self.getDescendantsByTagName(node, 'email'):
            self.expungeAttributes(e)
            e.tagName = 'a'
            mailto = 'mailto:{0}'.format(utils.nodeText(e))
            e.setAttribute('href', mailto)
        #Ext-links often declare their address as xlink:href attribute
        #if that fails, direct the link to the contained text
        for e in self.getDescendantsByTagName(node, 'ext-link'):
            eid = e.getAttribute('id')
            xh = e.getAttribute('xlink:href')
            self.expungeAttributes(e)
            if xh:
                e.setAttribute('href', xh)
            else:
                e.setAttribute('href', utils.nodeText(e))
            if eid:
                e.setAttribute('id', eid)
        #Uris often declare their address as xlink:href attribute
        #if that fails, direct the link to the contained text
        for u in self.getDescendantsByTagName(node, 'uri'):
            xh = u.getAttribute('xlink:href')
            self.expungeAttributes(u)
            if xh:
                u.setAttribute('href', xh)
            else:
                u.setAttribute('href', utils.nodeText(u))

    def makeFragmentIdentifiers(self):
        """
        This will create useful fragment identifier strings.
        """
        self.synop_frag = 'synop.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.main_frag = 'main.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.bib_frag = 'biblio.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.tab_frag = 'tables.{0}.xml'.format(self.doi_frag) + '#{0}'

    def convertFigElements(self, node):
        """
        <fig> tags are not allowed in OPS documents, the tagname must be
        converted to <img> and some conversion of the element's content model
        should be employed to make nice figures.
        """
        for f in self.getDescendantsByTagName(node, 'fig'):
            #We'll extract certain key data from the <fig> node in order to
            #construct the desired representation. The original node and its
            #descendants will be removed
            #First collect all attributes
            f_attrs = self.getAllAttributes(f, remove=False)
            try:
                label = f.getElementsByTagName('label')[0]
            except IndexError:
                label = ''
            else:
                label = utils.nodeText(label)
            try:
                caption = f.getElementsByTagName('caption')[0]
            except IndexError:
                caption = None
            graphic = f.getElementsByTagName('graphic')[0]
            graphic_xh = graphic.getAttribute('xlink:href')
            #Now we can begin constructing our OPS representation
            parent = f.parentNode
            parent.insertBefore(self.doc.createElement('hr'), f)
            img = self.doc.createElement('img')
            parent.insertBefore(img, f)
            img.setAttribute('alt', 'A figure')
            img.setAttribute('id', f_attrs['id'])
            #Compute the image source
            img_dir = 'images-' + self.doi_frag + '/figures/'
            img_name = os.path.splitext(graphic_xh)[0][-4:] + '.jpg'
            img.setAttribute('src', img_dir + img_name)
            #Now we can handle the caption and label
            if caption or label:
                div = self.doc.createElement('div')
                parent.insertBefore(div, f)
                div.setAttribute('class', 'caption')
                if label:
                    cap_lbl = self.appendNewElement('b', div)
                    self.appendNewText(label + '.', cap_lbl)
                if caption:
                    if caption.firstChild.tagName == 'p':
                        for cn in caption.firstChild.childNodes:
                            div.appendChild(cn.cloneNode(deep=True))
                    else:
                        for cn in caption.childNodes:
                            div.appendChild(cn.cloneNode(deep=True))
            #Remove the original <fig>
            parent.insertBefore(self.doc.createElement('hr'), f)
            parent.removeChild(f)

    def convertTableWrapElements(self, node):
        """
        <table-wrap> tags are not allowed in OPS documents. We want to do some
        processing of them in order to make nice OPS.
        """
        for t in self.getDescendantsByTagName(node, 'table-wrap'):
            #We'll extract certain key data from the <table-wrap> node in order
            #to construct the desired representation. The original node and its
            #descendants will be removed
            #First collect all attributes
            t_attrs = self.getAllAttributes(t, remove=False)
            #Get the optional label as text
            try:
                label = t.getElementsByTagName('label')[0]
            except IndexError:
                label = ''
            else:
                label = utils.nodeText(label)
            #Get the optional caption as xml or None
            try:
                caption = t.getElementsByTagName('caption')[0]
            except IndexError:
                caption = None
            #Get the optional table-wrap-foot as xml or none
            try:
                t_foots = t.getElementsByTagName('table-wrap-foot')
            except IndexError:
                t_foots = []
            #Now we can begin constructing our OPS representation
            parent = t.parentNode
            parent.insertBefore(self.doc.createElement('hr'), t)
            img = self.doc.createElement('img')
            parent.insertBefore(img, t)
            img.setAttribute('alt', 'A table')
            img.setAttribute('id', t_attrs['id'])
            #Compute the image source
            tid = t_attrs['id']
            if tid[0] == 'T':
                num = tid[1:]
            else:
                raise InputError('Unexpected table frag id in this article')
            img_dir = 'images-' + self.doi_frag + '/tables/'
            img_name = 't' + num.zfill(3) + '.jpg'
            img.setAttribute('src', img_dir + img_name)
            #Now we can handle the caption and label
            if caption or label:
                div = self.doc.createElement('div')
                parent.insertBefore(div, t)
                div.setAttribute('class', 'caption')
                if label:
                    cap_lbl = self.appendNewElement('b', div)
                    self.appendNewText(label + '.', cap_lbl)
                if caption:
                    if caption.firstChild.tagName == 'p':
                        for cn in caption.firstChild.childNodes:
                            div.appendChild(cn.cloneNode(deep=True))
                    else:
                        for cn in caption.childNodes:
                            div.appendChild(cn.cloneNode(deep=True))
            #Add the html version of the table to the html tables list
            #Note that <table-wrap_foot> nodes are given to the last table
            #node before appending to the html_tables list
            table = t.getElementsByTagName('table')[0]
            table.setAttribute('id', t_attrs['id'])
            for t_foot in t_foots:
                t_foot.tagName = 'div'
                t_foot.setAttribute('class', 'table-footnotes')
                table.appendChild(t_foot)
            #Create a link back to main text
            l = self.appendNewElement('div', table)
            p = self.appendNewElement('p', l)
            a = self.appendNewElement('a', p)
            a.setAttribute('href', self.main_frag.format(tid))
            self.appendNewText('Back to the text', a)
            self.html_tables.append(table)
            #Create a link to the html version of the table
            a = self.doc.createElement('a')
            a.setAttribute('href', self.tab_frag.format(tid))
            self.appendNewText('HTML version of this table', a)
            parent.insertBefore(a, t)
            #Remove the original <table-wrap>
            parent.insertBefore(self.doc.createElement('hr'), t)
            parent.removeChild(t)

    def convertXrefElements(self, node):
        """
        xref elements are used for internal referencing to document components
        such as figures, tables, equations, bibliography, or supplementary
        materials. As <a> is the only appropiate hypertext linker, this method
        converts xrefs to anchors with the appropriate address.
        """
        #This is a mapping of values of the ref-type attribute to the desired
        #local file to be addressed
        ref_map = {u'bibr': self.bib_frag,
                   u'fig': self.main_frag,
                   u'supplementary-material': self.main_frag,
                   u'table': self.main_frag,
                   u'aff': self.synop_frag,
                   u'sec': self.main_frag,
                   u'table-fn': self.tab_frag,
                   u'boxed-text': self.main_frag,
                   u'other': self.main_frag,
                   u'disp-formula': self.main_frag}
        for x in self.getDescendantsByTagName(node, 'xref'):
            x.tagName = 'a'
            x_attrs = self.getAllAttributes(x, remove=True)
            ref_type = x_attrs['ref-type']
            rid = x_attrs['rid']
            address = ref_map[ref_type].format(rid)
            x.setAttribute('href', address)

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSFrontiers')
