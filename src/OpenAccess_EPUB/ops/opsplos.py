"""
This module defines an OPS content generator class for PLoS. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import OpenAccess_EPUB.utils as utils
from opsmeta import OPSMeta
import os.path
import logging

log = logging.getLogger('OPSPLoS')

class InputError(Exception):
    """
    This is a custom exception for unexpected input from a publisher.
    """
    def __init__(self, detail):
        self.detail = detail

    def __str__(self):
        return self.detail


class OPSPLoS(OPSMeta):
    """
    This provides the full feature set to create OPS content for an ePub file
    from a PLoS journal article.
    """
    def __init__(self, article, output_dir):
        OPSMeta.__init__(self)
        log.info('Initiating OPSPLoS')
        print('Generating OPS content...')
        self.article = article.root_tag
        self.metadata = article.metadata
        self.doi = article.getDOI()
        #From "10.1371/journal.pone.0035956" get "pone.0335956"
        self.doi_frag = self.doi.split('10.1371/')[1]
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
        #Make the synopsis file and get its body element
        self.doc = self.make_document('synop')
        body = self.doc.getElementsByTagName('body')[0]

        #Create a large title element for the article
        self.make_synopsis_title(body)

        #Compile the list of authors and editors
        authors = self.get_authors_list()
        editors = self.get_editors_list()

        #Construct the authors section of the synopsis
        self.make_synopsis_authors(authors, body)

        #Construct the content for abstracts
        self.make_synopsis_abstracts(body)

        #Add a visual cue that the article info is distinct
        self.appendNewElement('hr', body)

        #Create the citation content
        self.make_synopsis_citation(body)

        #Create the editors section of the synopsis
        self.make_synopsis_editors(editors, body)

        #Post processing node conversion
        self.convert_emphasis_elements(body)
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

        #Handle node conversion
        #self.convertFigElements(body)
        #self.convertTableWrapElements(body)
        #self.convertListElements(body)
        #self.convertSecElements(body)
        #self.recursiveConvertDivTitles(body, depth=0)
        self.convert_emphasis_elements(body)
        self.convert_address_linking_elements(body)
        self.convert_xref_elements(body)
        #self.convertDispFormulaElements(body)
        #self.convertInlineFormulaElements(body)

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

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.bib_frag[:-4]), 'w') as op:
            op.write(self.doc.toprettyxml(encoding='utf-8'))

    def create_tables(self):
        """
        This method encapsulates the functions necessary to create a file
        containing html versions of all the tables in the article. If there
        are no tables, the file is not created.
        """

        self.doc = self.make_document('tables')
        body = self.doc.getElementsByTagName('body')[0]

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

    def convert_address_linking_elements(self, node):
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
            e.tagName = 'a'
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
            u.tagName = 'a'
            xh = u.getAttribute('xlink:href')
            self.expungeAttributes(u)
            if xh:
                u.setAttribute('href', xh)
            else:
                u.setAttribute('href', utils.nodeText(u))

    def make_fragment_identifiers(self):
        """
        This will create useful fragment identifier strings.
        """
        self.synop_frag = 'synop.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.main_frag = 'main.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.bib_frag = 'biblio.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.tab_frag = 'tables.{0}.xml'.format(self.doi_frag) + '#{0}'

    def convert_xref_elements(self, node):
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
                   u'disp-formula': self.main_frag,
                   u'fn': self.main_frag,
                   u'app': self.main_frag}
        for x in self.getDescendantsByTagName(node, 'xref'):
            x.tagName = 'a'
            x_attrs = self.getAllAttributes(x, remove=True)
            ref_type = x_attrs['ref-type']
            rid = x_attrs['rid']
            address = ref_map[ref_type].format(rid)
            x.setAttribute('href', address)

    ### Content Conversion Methods ###
    ##################################

    def make_synopsis_title(self, body):
        """
        Makes the title for the synopsis.
        """
        title = self.appendNewElement('h1', body)
        self.setSomeAttributes(title, {'id': 'title',
                                       'class': 'article-title'})
        title.childNodes = self.metadata.title.article_title.childNodes

    def get_authors_list(self):
        """
        Gets a list of all authors described in the metadata.
        """
        authors = []
        for contrib in self.metadata.contrib:
            if contrib.attrs['contrib-type'] == 'author':
                authors.append(contrib)
            else:
                if not contrib.attrs['contrib-type']:
                    print('No contrib-type provided for contibutor!')
                else:
                    print('Unexpected value for contrib-type')
        return authors

    def get_editors_list(self):
        """
        Gets a list of all editors described in the metadata.
        """
        editors = [i for i in self.metadata.contrib if i.attrs['contrib-type']=='editor']
        #editors = []
        #for contrib in self.metadata.contrib:
        #    if contrib.attrs['contrib-type'] == 'editor':
        #        editors.append(contrib)
        #    else:
        #        if not contrib.attrs['contrib-type']:
        #            print('No contrib-type provided for contibutor!')
        #        else:
        #            print('Unexpected value for contrib-type')
        return editors

    def make_synopsis_authors(self, authors, body):
        """
        Constructs the authors content after the title in of the synopsis;
        creates nodes and text.
        """
        #Make and append a new element to the passed body node
        author_element = self.appendNewElement('h3', body)
        author_element.setAttribute('class', 'authors')
        #Construct content for the author element
        first = True
        for author in authors:
            if first:
                first = False
            else:
                self.appendNewText(', ', author_element)
            if not author.anonymous:
                name = author.name[0].given + ' ' + author.name[0].surname
            else:
                name = 'Anonymous'
            self.appendNewText(name, author_element)
            for xref in author.xref:
                if xref.ref_type in ['corresp', 'aff']:
                    try:
                        sup_element = self.getChildrenByTagName('sup', xref.node)[0]
                    except IndexError:
                        log.info('Author xref did not contain <sup> element')
                        #sup_text = utils.nodeText(xref.node)
                        sup_text = ''
                    else:
                        sup_text = utils.nodeText(sup_element)
                    new_sup = self.appendNewElement('sup', author_element)
                    sup_link = self.appendNewElement('a', new_sup)
                    sup_link.setAttribute('href', self.synop_frag.format(xref.rid))
                    self.appendNewText(sup_text, sup_link)

    def make_synopsis_abstracts(self, body):
        """
        An article may contain data for various kinds of abstracts. This method
        works on those that are included in the synopsis, handling the content
        conversion and the ordering.
        """
        for abstract in self.metadata.abstract:
            if abstract.type == '':  # If no type is listed -> main abstract
                self.expungeAttributes(abstract.node)
                self.appendNewElementWithText('h2', 'Abstract', body)
                body.appendChild(abstract.node)
                abstract.node.tagName = 'div'
                abstract.node.setAttribute('id', 'abstract')
            if abstract.type == 'summary':
                self.expungeAttributes(abstract.node)
                self.appendNewElementWithText('h2', 'Author Summary', body)
                body.appendChild(abstract.node)
                abstract.node.tagName = 'div'
                abstract.node.setAttribute('id', 'author-summary')

    def make_synopsis_citation(self, body):
        """
        Creates a citation node for the synopsis of the article.
        """
        citation_text = self.format_self_citation()
        citation_div = self.appendNewElement('div', body)
        citation_div.setAttribute('id', 'article-citation')
        self.appendNewElementWithText('b', 'Citation: ', citation_div)
        self.appendNewText(citation_text, citation_div)

    def make_synopsis_editors(self, editors, body):
        if not editors:
            pass
        else:
            editors_div = self.appendNewElement('div', body)
            if len(editors) > 1:
                self.appendNewElementWithText('b', 'Editors: ', editors_div)
            else:
                self.appendNewElementWithText('b', 'Editor: ', editors_div)
            first = True
            for editor in editors:
                if first:
                    first = False
                else:
                    self.appendNewText('; ', editors_div)
                if not editor.anonymous:
                    name = editor.name[0].given + ' ' + editor.name[0].surname
                else:
                    name = 'Anonymous'
                self.appendNewText(name, editors_div)
                #Add some text for the editor affiliations
                for xref in editor.xref:
                    if xref.ref_type == 'aff':
                        #Relate this xref to the appropriate aff tag
                        ref_id = xref.rid
                        refer_aff = self.metadata.affs_by_id[ref_id]
                        #Put in appropriate text
                        self.appendNewText(', ', editors_div)
                        addr = refer_aff.getElementsByTagName('addr-line')[0]
                        editors_div.childNodes += addr.childNodes

    def format_self_citation(self):
        """
        PLoS articles present a citation for the article itself. This method
        will return the citation for the article as a string.
        """
        #This is not yet fully implemented.
        #I need clarification/documentation from PLoS
        #So for now I just put in the DOI
        return self.doi

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSPLoS')
