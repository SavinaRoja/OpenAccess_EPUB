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

        #Construct the authors affiliation section
        self.make_synopsis_affiliations(body)

        #Construct the content for abstracts
        self.make_synopsis_abstracts(body)

        #Add a visual cue that the article info is distinct
        self.appendNewElement('hr', body)

        #Create the citation content
        self.make_synopsis_citation(body)

        #Create the editors section of the synopsis
        self.make_synopsis_editors(editors, body)

        #Create the important dates section
        self.make_synopsis_dates(body)

        #Create the copyright statement
        self.make_synopsis_copyright(body)

        #Create the funding section
        self.make_synopsis_funding(body)

        #Create the competing interests statement
        self.make_synopsis_competing_interests(body)

        #Create the content for the article's correspondence
        self.make_synopsis_correspondences(body)

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
            if author.collab:  # If collab, just add rich content
                #Assume only one collab
                author_element.childNodes += author.collab[0].childNodes
            elif not author.anonymous:
                name = author.name[0].given + ' ' + author.name[0].surname
                self.appendNewText(name, author_element)
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

    def make_synopsis_affiliations(self, body):
        """
        Makes the content that displays affiliations.
        """
        if self.metadata.affs:
            affs_div = self.appendNewElement('div', body)
            affs_div.setAttribute('id', 'affiliations')

        #A simple way that seems to work by PLoS convention, but does not treat
        #the full scope of the <aff> element
        for aff in self.metadata.affs:
            aff_id = aff.getAttribute('id')
            if not 'aff' in aff_id:  # Skip affs for editors...
                continue
            #Get the label node and the addr-line node
            #<label> might be missing, especially for one author works
            label_node = self.getChildrenByTagName('label', aff)
            #I expect there to always be the <addr-line>
            addr_line_node = self.getChildrenByTagName('addr-line', aff)[0]
            cur_aff_span = self.appendNewElement('span', affs_div)
            cur_aff_span.setAttribute('id', aff_id)
            if label_node:
                label_text = utils.nodeText(label_node[0])
                label_b = self.appendNewElementWithText('b', label_text, cur_aff_span)
            addr_line_text = utils.nodeText(addr_line_node)
            self.appendNewText(addr_line_text + ', ', cur_aff_span)

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
        if not editors:  # No editors
            return
        editors_div = self.appendNewElement('div', body)
        if len(editors) > 1:  # Pluralize if more than one editor
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

    def make_synopsis_dates(self, body):
        """
        Makes the section containing important dates for the article: typically
        Received, Accepted, and Published.
        """
        dates_div = self.appendNewElement('div', body)
        dates_div.setAttribute('id', 'article-dates')

        #Received - Optional
        received = self.metadata.history['received']
        if received:
            self.appendNewElementWithText('b', 'Received: ', dates_div)
            self.appendNewText(self.format_date_string(received), dates_div)

        #Accepted - Optional
        accepted = self.metadata.history['accepted']
        if accepted:
            self.appendNewElementWithText('b', 'Accepted: ', dates_div)
            self.appendNewText(self.format_date_string(accepted), dates_div)

        #Published - Required
        published = self.metadata.pub_date['epub']
        self.appendNewElementWithText('b', 'Published: ', dates_div)
        self.appendNewText(self.format_date_string(published), dates_div)

    def make_synopsis_copyright(self, body):
        """
        Makes the copyright section for the ArticleInfo. For PLoS, this means
        handling the information contained in the metadata <permissions>
        element.
        """
        permissions = self.metadata.permissions
        if not permissions:
            return
        copyright_div = self.appendNewElement('div', body)
        copyright_div.setAttribute('id', 'copyright')
        self.appendNewElementWithText('b', 'Copyright: ', body)

        #Construct the string for the copyright statement
        copyright_string = u' \u00A9 '
        #I expect year to always be there
        copyright_string += utils.nodeText(permissions.year) + ' '
        #Holder won't always be there
        if permissions.holder:
            copyright_string += utils.nodeText(permissions.holder) + '.'
        #I don't know if the license will always be included
        if permissions.license:  # I hope this is a general solution
            license_p = self.getChildrenByTagName('license-p', permissions.license)[0]
            copyright_string += ' ' + utils.nodeText(license_p)
        self.appendNewText(copyright_string, body)

    def make_synopsis_funding(self, body):
        """
        Creates the element for declaring Funding in the article info.
        """
        funding = self.metadata.funding_group
        if not funding:
            return
        funding_div = self.appendNewElement('div', body)
        funding_div.setAttribute('id', 'funding')
        self.appendNewElementWithText('b', 'Funding: ', funding_div)
        #As far as I can tell, PLoS only uses one funding-statement
        funding_div.childNodes += funding[0].funding_statement[0].childNodes

    def make_synopsis_competing_interests(self, body):
        """
        Creates the element for declaring competing interests in the article
        info.
        """
        #Check for author-notes
        author_notes = self.metadata.author_notes
        if not author_notes:  # skip if not found
            return
        #Check for conflict of interest statement
        fn_nodes = self.getChildrenByTagName('fn', author_notes)
        conflict = None
        for fn in fn_nodes:
            if fn.getAttribute('fn-type') == 'conflict':
                conflict = fn
        if not conflict:  # skip if not found
            return
        #Go about creating the content
        conflict_div = self.appendNewElement('div', body)
        conflict_div.setAttribute('id', 'conflict')
        self.appendNewElementWithText('b', 'Competing Interests: ', conflict_div)
        conflict_p = self.getChildrenByTagName('p', conflict)[0]
        conflict_div.childNodes += conflict_p.childNodes

    def make_synopsis_correspondences(self, body):
        """
        Articles generally provide a first contact, typically an email address
        for one of the authors. This will supply that content.
        """
        #Check for author-notes
        author_notes = self.metadata.author_notes
        if not author_notes:  # skip if not found
            return
        #Check for correspondences
        correspondence = self.getChildrenByTagName('corresp', author_notes)
        if not correspondence:  # skip if none found
            return
        #Go about creating the content
        corresp_div = self.appendNewElement('div', body)
        corresp_div.setAttribute('id', 'correspondence')
        for corresp_fn in correspondence:
            corresp_subdiv = self.appendNewElement('div', corresp_div)
            corresp_subdiv.setAttribute('id', corresp_fn.getAttribute('id'))
            corresp_subdiv.childNodes = corresp_fn.childNodes

    def format_date_string(self, date_tuple):
        """
        Receives a date_tuple object, defined in jptsmeta, and outputs a string
        for placement in the article content.
        """
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        date_string = ''
        if date_tuple.season:
            return '{0}, {1}'.format(date_tuple.season, date_tuple.year)
        else:
            if not date_tuple.month and not date_tuple.day:
                return '{0}'.format(date_tuple.year)
            if date_tuple.month:
                date_string += months[int(date_tuple.month)]
            if date_tuple.day:
                date_string += ' ' + date_tuple.day
            return ', '.join([date_string, date_tuple.year])

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
