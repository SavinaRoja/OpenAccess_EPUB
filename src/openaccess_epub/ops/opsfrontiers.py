# -*- coding: utf-8 -*-
"""
This module defines an OPS content generator class for Frontiers. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import openaccess_epub.utils as utils
from openaccess_epub.ops.opsmeta import OPSMeta
import os.path
import logging

log = logging.getLogger('OPSFrontiers')


class OPSFrontiers(OPSMeta):
    """
    This provides the full feature set to create OPS content for an ePub file
    from a Frontiers journal article.
    """
    def __init__(self, article, output_dir):
        OPSMeta.__init__(self)
        log.info('Initiating OPSFrontiers')
        print('Generating OPS content...')
        self.article = article.root_tag
        self.metadata = article.metadata
        self.doi = article.getDOI()
        #From "10.3389/fimmu.2012.00104" get "fimmu.2012.00104"
        self.doi_frag = self.doi.split('10.3389/')[1]
        self.make_fragment_identifiers()
        self.ops_dir = os.path.join(output_dir, 'OPS')
        self.html_tables = []
        self.create_synopsis()
        self.create_main()
        self.create_biblio()
        if self.html_tables:
            self.create_tables()

    def create_synopsis(self):
        """
        This method encapsulates the functions necessary to create the synopsis
        segment of the article.
        """
        self.doc = self.make_document('synop')
        body = self.doc.getElementsByTagName('body')[0]

        #Create the title for the article
        title = self.appendNewElement('h1', body)
        self.setSomeAttributes(title, {'id': 'title',
                                       'class': 'article-title'})
        title.childNodes = self.metadata.title.article_title.childNodes

        #Get authors
        self.auths = []
        for contrib in self.metadata.contrib:
            if contrib.attrs['contrib-type'] == 'author':
                self.auths.append(contrib)
            else:
                if not contrib.attrs['contrib-type']:
                    print('No contrib-type provided for contibutor!')
                else:
                    print('Unexpected value for contrib-type')

        #Parse authors into formatted xml
        auth_el = self.appendNewElement('h3', body)
        auth_el.setAttribute('class', 'authors')
        first = True
        for auth in self.auths:
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
                    log.warning('Could not identify affiliation number!')
                    sup_text = ''
            else:
                sup_text = utils.nodeText(sup)
            if aff.getAttribute('id'):
                affp.setAttribute('id', aff.getAttribute('id'))
            if sup_text:
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
            self.expungeAttributes(abstract.node)
            abstract.node.tagName = 'div'
            abstract.node.setAttribute('id', 'abstract')

        #Refer to self.create_article_info()
        self.create_article_info(body)

        #Post processing node conversion
        self.convertEmphasisElements(body)
        self.convert_address_linking_elements(body)
        self.convert_xref_elements(body)

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.synop_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def create_main(self):
        """
        This method encapsulates the functions necessary to create the main
        segment of the article.
        """

        self.doc = self.make_document('main')
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
        try:
            back = self.article.getElementsByTagName('back')[0]
        except IndexError:
            pass
        else:
            if back.getElementsByTagName('ack'):
                div = self.doc.createElement('div')
                div.setAttribute('id', 'OA-EPUB-ack')
                h = self.appendNewElement('title', div)
                self.appendNewText('Acknowledgments', h)
                ack = back.getElementsByTagName('ack')[0]
                p = ack.getElementsByTagName('p')[0]
                for cn in p.childNodes:
                    div.appendChild(cn.cloneNode(deep=True))
                body.appendChild(div)
            if back.getElementsByTagName('fn'):
                div = self.doc.createElement('div')
                div.setAttribute('id', 'OA-EPUB-fn')
                h = self.appendNewElement('title', div)
                self.appendNewText('Footnotes', h)
                for fn in back.getElementsByTagName('fn'):
                    fid = fn.getAttribute('id')
                    new_p = self.appendNewElement('p', div)
                    new_p.setAttribute('id', fid)
                    p = fn.getElementsByTagName('p')[0]
                    for cn in p.childNodes:
                        new_p.appendChild(cn.cloneNode(deep=True))
                body.appendChild(div)
            for app in back.getElementsByTagName('app'):
                div = self.doc.createElement('div')
                div.setAttribute('id', app.getAttribute('id'))
                for cn in app.childNodes:
                    div.appendChild(cn.cloneNode(deep=True))
                body.appendChild(div)

        #Handle node conversion
        self.convertFigElements(body)
        self.convertTableWrapElements(body)
        self.convertListElements(body)
        self.convert_sec_elements(body)
        self.recursiveConvertDivTitles(body, depth=0)
        self.convertEmphasisElements(body)
        self.convert_address_linking_elements(body)
        self.convert_xref_elements(body)
        self.convertDispFormulaElements(body)
        self.convertInlineFormulaElements(body)

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.main_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def create_biblio(self):
        """
        This method encapsulates the functions necessary to create the biblio
        segment of the article.
        """

        self.doc = self.make_document('biblio')
        body = self.doc.getElementsByTagName('body')[0]
        body.setAttribute('id', 'references')
        try:
            back = self.article.getElementsByTagName('back')[0]
        except IndexError:
            return None
        else:
            refs = back.getElementsByTagName('ref')
        if not refs:
            return None
        refnum = 1
        for ref in refs:
            p = self.appendNewElement('p', body)
            self.appendNewText('{0}. '.format(refnum), p)
            refnum += 1
            p.setAttribute('id', ref.getAttribute('id'))
            self.appendNewText(utils.serializeText(ref, []), p)

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.bib_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def create_tables(self):
        """
        This method encapsulates the functions necessary to create a file
        containing html versions of all the tables in the article. If there
        are no tables, the file is not written.
        """

        self.doc = self.make_document('tables')
        body = self.doc.getElementsByTagName('body')[0]
        for table in self.html_tables:
            label = table.getAttribute('label')
            if label:
                table.removeAttribute('label')
                l = self.appendNewElement('div', body)
                b = self.appendNewElement('b', l)
                self.appendNewText(label, b)
            #Move the table to the body
            body.appendChild(table)
            for d in table.getElementsByTagName('div'):
                body.appendChild(d)
                #Move the link back to the body
                #body.appendChild(table.lastChild)
        #Handle node conversion
        self.convertEmphasisElements(body)
        self.convertDispFormulaElements(body)
        self.convertInlineFormulaElements(body)
        self.convert_xref_elements(body)

        with open(os.path.join(self.ops_dir, self.tab_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def create_article_info(self, body):
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
        ainfo.appendChild(self.renderCitation())
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
            #KNOWN BUG: some current address data is listed as a corresp and
            #is formatted differently.
            try:
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
            except:
                pass

    def make_fragment_identifiers(self):
        """
        This will create useful fragment identifier strings.
        """
        self.synop_frag = 'synop.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.main_frag = 'main.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.bib_frag = 'biblio.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.tab_frag = 'tables.{0}.xml'.format(self.doi_frag) + '#{0}'

    def convertListElements(self, node):
        """
        <list> tags are not allowed in OPS documents, the tagname may be
        converted to <ol> or <ul> for ordered and unordered lists respectively.
        The <list> tag should contain a "list-type" attribute to declare the
        appropriate type. Attributes are not to be kept.
        """
        for l in self.getDescendantsByTagName(node, 'list'):
            l_attrs = self.getAllAttributes(l, remove=True)
            try:
                if l_attrs['list-type'] == 'order':
                    l.tagName = 'ol'
                elif l_attrs['list-type'] == 'bullet':
                    l.tagName = 'ul'
            except KeyError:
                l.tagName = 'ul'
            else:
                for li in self.getChildrenByTagName('list-item', l):
                    li.tagName = 'li'

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
            #Coerce the file extension to .jpg
            graphic_xh = os.path.splitext(graphic_xh)[0] + '.jpg'
            #Now we can begin constructing our OPS representation
            parent = f.parentNode
            parent.insertBefore(self.doc.createElement('hr'), f)
            img = self.doc.createElement('img')
            parent.insertBefore(img, f)
            img.setAttribute('alt', 'A figure')
            img.setAttribute('id', f_attrs['id'])
            #Compute the image source
            img_dir = 'images/'
            img.setAttribute('src', img_dir + graphic_xh)
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
            t_foots = t.getElementsByTagName('table-wrap-foot')
            #Get <fn> tags for conversion to <span>
            fns = t.getElementsByTagName('fn')
            #Now we can begin constructing our OPS representation
            parent = t.parentNode
            parent.insertBefore(self.doc.createElement('hr'), t)
            img = self.doc.createElement('img')
            parent.insertBefore(img, t)
            img.setAttribute('alt', 'A table')
            img.setAttribute('id', t_attrs['id'])
            #Add the image source, this is a little complex, see the method
            src = self.tableSource(t_attrs['id'])
            img.setAttribute('src', src)
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
            if label:
                table.setAttribute('label', label)
            for t_foot in t_foots:
                t_foot.tagName = 'div'
                t_foot.setAttribute('class', 'table-footnotes')
                table.appendChild(t_foot)
            for fn in fns:
                fn_parent = fn.parentNode
                fn_id = fn.getAttribute('id')
                first = True
                for fc in fn.childNodes:
                    fn_parent.insertBefore(fc, fn)
                    if first:
                        fc.setAttribute('id', fn_id)
                        first = False
                fn_parent.removeChild(fn)
            #Create a link back to main text
            l = self.appendNewElement('div', table)
            p = self.appendNewElement('p', l)
            a = self.appendNewElement('a', p)
            a.setAttribute('href', self.main_frag.format(t_attrs['id']))
            self.appendNewText('Back to the text', a)
            self.html_tables.append(table)
            #Create a link to the html version of the table
            a = self.doc.createElement('a')
            a.setAttribute('href', self.tab_frag.format(t_attrs['id']))
            self.appendNewText('HTML version of this table', a)
            parent.insertBefore(a, t)
            #Remove the original <table-wrap>
            parent.insertBefore(self.doc.createElement('hr'), t)
            parent.removeChild(t)

    def convert_xref_elements(self, node):
        """
        xref elements are used for internal referencing to document components
        such as figures, tables, equations, bibliography, or supplementary
        materials. As <a> is the only appropiate hypertext linker, this method
        converts xrefs to anchors with the appropriate address.
        """
        #This is a mapping of values of the ref-type attribute to the desired
        #local file to be addressed
        ref_map = {'bibr': self.bib_frag,
                   'fig': self.main_frag,
                   'supplementary-material': self.main_frag,
                   'table': self.main_frag,
                   'aff': self.synop_frag,
                   'sec': self.main_frag,
                   'table-fn': self.tab_frag,
                   'boxed-text': self.main_frag,
                   'other': self.main_frag,
                   'disp-formula': self.main_frag,
                   'fn': self.main_frag,
                   'app': self.main_frag}
        for x in self.getDescendantsByTagName(node, 'xref'):
            x.tagName = 'a'
            x_attrs = self.getAllAttributes(x, remove=True)
            ref_type = x_attrs['ref-type']
            rid = x_attrs['rid']
            address = ref_map[ref_type].format(rid)
            x.setAttribute('href', address)

    def convert_sec_elements(self, node):
        """
        <sec> elements must be converted to meaningful <div> nodes
        """
        c = 0
        for s in self.getDescendantsByTagName(node, 'sec'):
            s.tagName = 'div'
            self.renameAttributes(s, [['sec-type', 'class']])
            if not s.getAttribute('id'):
                s.setAttribute('id', 'OA-EPUB-{0}'.format(str(c)))
                c += 1

    def convertDispFormulaElements(self, node):
        """
        <disp-formula> elements must be converted to conforming ops swtich
        elements.
        """
        for df in self.getDescendantsByTagName(node, 'disp-formula'):
            #remove label
            label = df.getElementsByTagName('label')
            for l in label:
                df.removeChild(l)
            dfid = df.getAttribute('id')
            df.tagName = 'ops:switch'
            oc = self.appendNewElement('ops:case', df)
            oc.setAttribute('required-namespace', 'http://www.w3.org/1998/Math/MathML')
            math = df.getElementsByTagName('mml:math')[0]
            oc.appendChild(math)
            math.setAttribute('xmlns:mml', 'http://www.w3.org/1998/Math/MathML')
            od = self.appendNewElement('ops:default', df)
            img = self.appendNewElement('img', od)
            img.setAttribute('alt', 'A Display Formula')
            #Compute the image source
            if dfid[0] == 'E':
                num = dfid[1:]
            else:
                raise InputError('Unexpected disp-formula frag id in this article')
            img_dir = 'images-' + self.doi_frag + '/equations/'
            img_name = 'e' + num.zfill(3) + '.gif'
            img.setAttribute('src', img_dir + img_name)
            img.setAttribute('class', 'disp-formula')

    def convertInlineFormulaElements(self, node):
        """
        <inline-formula> elements must be converted to conforming ops swtich
        elements.
        """
        for f in self.getDescendantsByTagName(node, 'inline-formula'):
            #remove label
            label = f.getElementsByTagName('label')
            for l in label:
                f.removeChild(l)
            f.tagName = 'ops:switch'
            oc = self.appendNewElement('ops:case', f)
            oc.setAttribute('required-namespace', 'http://www.w3.org/1998/Math/MathML')
            math = f.getElementsByTagName('mml:math')[0]
            fid = math.getAttribute('id')
            oc.appendChild(math)
            math.setAttribute('xmlns:mml', 'http://www.w3.org/1998/Math/MathML')
            od = self.appendNewElement('ops:default', f)
            img = self.appendNewElement('img', od)
            img.setAttribute('alt', 'An Inline Formula')
            #Compute the image source
            if fid[0] == 'M':
                num = fid[1:]
            else:
                raise InputError('Unexpected disp-formula frag id in this article')
            img_dir = 'images-' + self.doi_frag + '/equations/'
            img_name = 'i' + num.zfill(3) + '.gif'
            img.setAttribute('src', img_dir + img_name)
            img.setAttribute('class', 'inline-formula')

    def renderCitation(self):
        """
        This method is responsible for producing properly formatted citations
        for Frontiers. This is specific for the citation string of the article
        itself. For bibliographic citations, please refer to
        renderBiblioCitation()
        """
        #Based on information from Frontiers, it appears that the citation
        #types to be concerned about are "Article in a periodical",
        #"Article in a book", and "Book". I think we can expect to follow the
        #guidelines for periodical article at this stage.
        citation = self.doc.createElement('p')
        b = self.appendNewElement('b', citation)
        self.appendNewText('Citation: ', b)
        auth_num = len(self.auths)
        if auth_num == 1:
            auth = self.auths[0]
            if not auth.anonymous:
                given_initial = auth.name[0].given[0] + '.'
                surname = auth.name[0].surname
                name = ', '.join([surname, given_initial])
            else:
                name = 'Anonymous.'
        elif auth_num == 2:
            names = []
            for auth in self.auths:
                if not auth.anonymous:
                    given_initial = auth.name[0].given[0] + '.'
                    surname = auth.name[0].surname
                    names.append(', '.join([surname, given_initial]))
                else:
                    names.append('Anonymous.')
            name = ', and '.join([names[0], names[1]])
        elif auth_num > 2:
            auth = self.auths[0]
            if not auth.anonymous:
                given_initial = auth.name[0].given[0] + '.'
                surname = auth.name[0].surname
                name = ', '.join([surname, given_initial])
            else:
                name = 'Anonymous.'
            name += ', et al.'
        else:
            name = 'Anonymous.'
        #The name is followed by the year in parentheses
        year = ' ({0}). '.format(self.metadata.pub_date['epub'].year)
        self.appendNewText(name + year, citation)
        #Next comes the article title, which can have complex children
        for cn in self.metadata.title.article_title.childNodes:
            citation.appendChild(cn.cloneNode(deep=True))
        self.appendNewText('. ', citation)
        ijrn = self.appendNewElement('i', citation)
        self.appendNewText(self.metadata.journal_id['publisher-id'], ijrn)
        #Add the volume of the journal in which the article was published
        volume = self.metadata.volume.value
        b = self.appendNewElement('b', citation)
        self.appendNewText(volume, b)
        #Add the elocation id of the article
        elocation_id = self.metadata.elocation_id
        self.appendNewText(':' + elocation_id + '. ', citation)
        #Add the doi of the article
        self.appendNewText(self.doi, citation)
        return citation

    def renderBiblioCitation(self, refnode):
        """
        This method is responsible for producing properly formatted
        bibliographic citations for Frontiers. It is called individually on
        each ref node in the back ref-list, and uses the contained xml content
        to return a node for appending to the bibliography.
        """
        #We will be employing the Chicago Manual of Style, contrary to the
        #practices in the PDF and online fulltext

        #citation types I have seen
        #journal, book, thesis, other, confproc, web
        citation = self.doc.createElement('p')
        citation.setAttribute('id', refnode.getAttribute('id'))
        cnode = refnode.getElementsByTagName('citation')[0]
        ctype = cnode.getAttribute('citation-type')
        if ctype in ['book', 'conf-proc', 'journal', 'thesis', 'web']:
            pg = cnode.getElementsByTagName('person-group')[0]
            names = pg.getElementsByTagName('name')
            names_num = len(names)
            if names_num == 1:
                n = names[0]
                s = utils.nodeText(n.getElementsByTagName('surname'))
                g = utils.nodeText(n.getElementsByTagName('given-names'))
                name = ', '.join([s, g])
            elif names_num == 2:
                nlist = []
                for name in (names[0], names[1]):
                    s = utils.nodeText(n.getElementsByTagName('surname'))
                    g = utils.nodeText(n.getElementsByTagName('given-names'))
                    nlist.append(', '.join([s, g]))
                name = ', and '.join([nlist[0], nlist[1]])
            elif names_num > 2:
                n = names[0]
                s = utils.nodeText(n.getElementsByTagName('surname'))
                g = utils.nodeText(n.getElementsByTagName('given-names'))
                name = ', '.join([s, g])
                name += ', et al.'
            else:
                name = 'Anonymous.'
            #Handle the year
            year = utils.nodeText(cnode.getElementsByTagName('year')[0])
            year = ' ({0}). '.format(year)
            self.appendNewText(name + year, citation)
        else:  #This handles unkown citation types
            print('Unhandled Bibliographic citation type ' + ctype)
            text = utils.serializeText(cnode, [])
            self.appendNewText(text, citation)
            return citation
        if ctype == 'book':
            source = cnode.getElementsByTagName('source')[0]
            source.tagName = 'i'
            citation.appendChild(source)
            pl = utils.nodeText(cnode.getElementsByTagName('publisher-loc'))[0]
            pn = utils.nodeText(cnode.getElementsByTagName('publisher-name'))[0]
            self.appendNewText('. {0}:{1}.'.format(pl, pn), citation)
            try:
                pub_id = cnode.getElementsByTagName('pub-id')[0]
            except IndexError:
                pass
            else:
                self.appendNewText(utils.nodeText(pub_id), citation)
        elif ctype == 'journal':
            at = cnode.getElementsByTagName('article-title')[0]
            for cn in at.childNodes:
                citation.appendChild(cn.cloneNode(deep=True))
            self.appendNewText('. ', citation)
            source = cnode.getElementsByTagName('source')[0]
            source.tagName = 'i'
            citation.appendChild(source)
            volume = cnode.getElementsByTagName('volume')[0]
        return citation

    def recursiveConvertDivTitles(self, node, depth=0):
        """
        A method for converting title tags to heading format tags
        """
        taglist = ['h2', 'h3', 'h4', 'h5', 'h6']
        for i in node.childNodes:
            try:
                tag = i.tagName
            except AttributeError:
                pass  # Text nodes have no tagName attribute
            else:
                if tag == 'div':
                    try:
                        divlabel = self.getChildrenByTagName('label', i)[0]
                    except IndexError:
                        label = ''
                    else:
                        if not divlabel.childNodes:
                            i.removeChild(divlabel)
                        else:
                            label = utils.nodeText(divlabel)
                            i.removeChild(divlabel)
                    try:
                        divtitle = i.getElementsByTagName('title')[0]
                    except IndexError:
                        pass
                    else:
                        if not divtitle.childNodes:
                            i.removeChild(divtitle)
                        else:
                            divtitle.tagName = taglist[depth]
                            if label:
                                l = self.doc.createTextNode(label)
                                divtitle.insertBefore(l, divtitle.firstChild)
                        depth += 1
                        self.recursiveConvertDivTitles(i, depth)
                        depth -= 1

    def tableSource(self, table_id):
        """
        As the name of the table image is not directly referenced in the input,
        this method is tasked with the job of finding the correct table image
        based on the table's id.
        """
        if table_id[:2] == 'TA':
            num = int(table_id[2:])
            pref = 'at'
        elif table_id[0] == 'T':
            num = int(table_id[1:])
            pref = 't'
        else:
            err_msg = 'Unknown table ID type: {0}'.format(table_id)
            log.error(err_msg)
            raise InputError(err_msg)
        img_dir = 'images/'
        for item in os.listdir(os.path.join(self.ops_dir, 'images')):
            root, ext = os.path.splitext(item)
            if ext == '.jpg':
                suffix = root.split('-')[-1]
                if suffix[0] == 't':
                    if 't' == pref and int(suffix[1:]) == num:
                        return(img_dir + item)
                elif suffix[:2] == 'at':
                    if 'at' == pref and int(suffix[2:]) == num:
                        return (img_dir + item)
        raise InputError('Could not find table image, ID {0}'.format(table_id))
