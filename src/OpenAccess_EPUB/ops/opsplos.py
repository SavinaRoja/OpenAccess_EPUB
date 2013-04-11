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
        self.backmatter = article.metadata.backmatter
        self.doi = article.getDOI()
        #From "10.1371/journal.pone.0035956" get "journal.pone.0335956"
        self.doi_frag = self.doi.split('10.1371/')[1]
        self.make_fragment_identifiers()
        self.ops_dir = os.path.join(output_dir, 'OPS')
        self.html_tables = []
        self.create_main()
        self.create_biblio()
        if self.html_tables:
            self.create_tables()

    def create_main(self):
        """
        This method encapsulates the process required to generate the primary
        body of the article. This includes the heading, article info, and main
        text, including some elements of the back matter. It does not include
        the bibliography or the separate tables document, both of which are
        technically optional and make sense as "nonlinear elements.
        """
        #The first job is to create a file and get a handle on its body element
        self.document = self.make_document('main')
        body = self.document.getElementsByTagName('body')[0]

        #The section that contains the Article Title, List of Authors and
        #Affiliations, and Abstracts is referred to as the Heading
        self.make_heading(body)

        #The ArticleInfo section contains the (self) Citation, Editors, Dates,
        #Copyright, Funding Statement, Competing Interests Statement,
        #Correspondence, and Footnotes. Maybe more...
        self.make_article_info(body)

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
        self.convert_disp_formula_elements(body)
        self.convert_inline_formula_elements(body)
        self.convert_named_content_elements(body)
        self.convert_disp_quote_elements(body)
        self.convert_emphasis_elements(body)
        self.convert_address_linking_elements(body)
        self.convert_xref_elements(body)
        self.convert_boxed_text_elements(body)
        self.convert_verse_group_elements(body)
        self.convert_supplementary_material_elements(body)
        self.convert_fn_elements(body)
        self.convert_def_list_elements(body)
        self.convert_ref_list_elements(body)
        self.convert_list_elements(body)

        self.convert_fig_elements(body)
        self.convert_table_wrap_elements(body)

        #TODO: Back matter stuffs

        #These come last for a reason
        self.convert_sec_elements(body)
        self.convert_div_titles(body)

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.main_frag[:-4]), 'w') as op:
            op.write(self.document.toxml(encoding='utf-8'))
            #op.write(self.document.toprettyxml(encoding='utf-8'))

    def make_heading(self, receiving_node):
        """
        The Heading includes the Article Title, List of Authors and
        Affiliations, and Abstracts.

        In terms of output content, this is the first element and is followed
        by the ArticleInfo.

        This function accepts the receiving_node argument, which will receive
        all generated output as new childNodes.
        """
        #Create a div for Heading, exposing it to linking and formatting
        heading_div = self.appendNewElement('div', receiving_node)
        heading_div.setAttribute('id', 'Heading')
        #Creation of the title
        self.make_heading_title(heading_div)
        #Creation of the Authors
        list_of_authors = self.get_authors_list()
        self.make_heading_authors(list_of_authors, heading_div)
        #Creation of the Authors Affiliations text
        self.make_heading_affiliations(heading_div)
        #Creation of the Abstract content for the Heading
        self.make_heading_abstracts(heading_div)

    def make_article_info(self, receiving_node):
        """
        The Article Info contains the (self) Citation, Editors, Dates,
        Copyright, Funding Statement, Competing Interests Statement,
        Correspondence, and Footnotes. Maybe more...

        This content follows the Heading and precedes the Main segment in the
        output.

        This function accepts the receiving_node argument, which will receive
        all generated output as new childNodes.
        """
        #Create a div for ArticleInfo, exposing it to linking and formatting
        article_info_div = self.appendNewElement('div', receiving_node)
        article_info_div.setAttribute('id', 'ArticleInfo')
        #Creation of the self Citation
        self.make_article_info_citation(article_info_div)
        #Creation of the Editors
        list_of_editors = self.get_editors_list()
        self.make_article_info_editors(list_of_editors, article_info_div)
        #Creation of the important Dates segment
        self.make_article_info_dates(article_info_div)
        #Creation of the Copyright statement
        self.make_article_info_copyright(article_info_div)
        #Creation of the Funding statement
        self.make_article_info_funding(article_info_div)
        #Creation of the Competing Interests statement
        self.make_article_info_competing_interests(article_info_div)
        #Creation of the Correspondences (contact information) for the article
        self.make_article_info_correspondences(article_info_div)
        #Creation of the Footnotes (other) for the ArticleInfo
        self.make_article_info_footnotes_other(article_info_div)

    def post_processing_node_conversion(self, node):
        """
        This is a top-level function for calling a suite of methods which
        translate JPTS 3.0 XML to OPS XML for PLoS content.

        These methods will search the DOM tree beneath the specified Node with
        its getElementsByTagName('tagname') method; they will find elements
        at any depth beneath the Node and attempt conversion/translation.
        """
        #This current listing was simply grabbed from the old create_synopsis
        #method and will receive later review and development
        #TODO: Review this function and decide what to do with it
        self.convert_emphasis_elements(node)
        self.convert_address_linking_elements(node)
        self.convert_xref_elements(node)
        self.convert_named_content_elements(node)
        self.convert_sec_elements(node)
        self.convert_div_titles(node, depth=1)

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
        for ref in refs:
            p = self.appendNewElement('p', body)
            p.setAttribute('id', ref.getAttribute('id'))
            self.appendNewText(utils.serializeText(ref, []), p)

        #Finally, write to a document
        with open(os.path.join(self.ops_dir, self.bib_frag[:-4]), 'w') as op:
            op.write(self.doc.toxml(encoding='utf-8'))
            #op.write(self.doc.toprettyxml(encoding='utf-8'))

    def create_tables(self):
        """
        This method encapsulates the functions necessary to create a file
        containing html versions of all the tables in the article. If there
        are no tables, the file is not created.
        """

        self.doc = self.make_document('tables')
        body = self.doc.getElementsByTagName('body')[0]

        for table in self.html_tables:
            if table.tagName == 'table-wrap-foot':
                foot_div = self.appendNewElement('div', body)
                foot_div.setAttribute('class', 'table-wrap-foot')
                foot_div.childNodes = table.childNodes
                continue
            label = table.getAttribute('label')
            if label:
                table.removeAttribute('label')
                label_div = self.appendNewElement('div', body)
                label_div_b = self.appendNewElement('b', label_div)
                self.appendNewText(label, label_div_b)
            #Move the table to the body
            body.appendChild(table)
            for d in table.getElementsByTagName('div'):
                body.appendChild(d)
                #Move the link back to the body
                #body.appendChild(table.lastChild)

        #Handle node conversion
        self.convert_emphasis_elements(body)
        self.convert_fn_elements(body)
        self.convert_disp_formula_elements(body)
        self.convert_inline_formula_elements(body)
        self.convert_xref_elements(body)

        with open(os.path.join(self.ops_dir, self.tab_frag[:-4]), 'w') as op:
            op.write(self.doc.toxml(encoding='utf-8'))
            #op.write(self.doc.toprettyxml(encoding='utf-8'))

    def make_fragment_identifiers(self):
        """
        This will create useful fragment identifier strings.
        """
        self.main_frag = 'main.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.bib_frag = 'biblio.{0}.xml'.format(self.doi_frag) + '#{0}'
        self.tab_frag = 'tables.{0}.xml'.format(self.doi_frag) + '#{0}'

    def get_authors_list(self):
        """
        Gets a list of all authors described in the metadata.
        """
        return [i for i in self.metadata.contrib if i.attrs['contrib-type']=='author']

    def get_editors_list(self):
        """
        Gets a list of all editors described in the metadata.
        """
        return [i for i in self.metadata.contrib if i.attrs['contrib-type']=='editor']

    def make_heading_title(self, receiving_node):
        """
        Makes the Article Title for the Heading.

        Metadata element, content derived from FrontMatter
        """
        title = self.appendNewElement('h1', receiving_node)
        self.setSomeAttributes(title, {'id': 'title',
                                       'class': 'article-title'})
        title.childNodes = self.metadata.title.article_title.childNodes

    def make_heading_authors(self, authors, receiving_node):
        """
        Constructs the Authors content for the Heading. This should display
        directly after the Article Title.

        Metadata element, content derived from FrontMatter
        """
        #Make and append a new element to the passed receiving_node
        author_element = self.appendNewElement('h3', receiving_node)
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
                    sup_link.setAttribute('href', self.main_frag.format(xref.rid))
                    self.appendNewText(sup_text, sup_link)

    def make_heading_affiliations(self, receiving_node):
        """
        Makes the content for the Author Affiliations, displays after the
        Authors segment in the Heading.

        Metadata element, content derived from FrontMatter
        """
        if self.metadata.affs:
            affs_div = self.appendNewElement('div', receiving_node)
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

    def make_heading_abstracts(self, receiving_node):
        """
        An article may contain data for various kinds of abstracts. This method
        works on those that are included in the Heading. This is displayed
        after the Authors and Affiliations.

        Metadata element, content derived from FrontMatter
        """
        for abstract in self.metadata.abstract:
            #Remove <title> elements in the abstracts
            for title in self.getChildrenByTagName('title', abstract.node):
                abstract.node.removeChild(title)
            if abstract.type == '':  # If no type is listed -> main abstract
                self.expungeAttributes(abstract.node)
                self.appendNewElementWithText('h2', 'Abstract', receiving_node)
                receiving_node.appendChild(abstract.node)
                abstract.node.tagName = 'div'
                abstract.node.setAttribute('id', 'abstract')
            if abstract.type == 'summary':
                self.expungeAttributes(abstract.node)
                self.appendNewElementWithText('h2', 'Author Summary', receiving_node)
                receiving_node.appendChild(abstract.node)
                abstract.node.tagName = 'div'
                abstract.node.setAttribute('id', 'author-summary')
            if abstract.type == 'editors-summary':
                self.expungeAttributes(abstract.node)
                self.appendNewElementWithText('h2', 'Editors\' Summary', receiving_node)
                receiving_node.appendChild(abstract.node)
                abstract.node.tagName = 'div'
                abstract.node.setAttribute('id', 'editors-summary')

    def make_article_info_citation(self, receiving_node):
        """
        Creates a self citation node for the ArticleInfo of the article.

        This method relies on self.format_self_citation() as an implementation
        of converting an article's metadata to a plain string, and then adds
        composes content for the display of that string in the ArticleInfo.
        """
        citation_text = self.format_self_citation()
        citation_div = self.appendNewElement('div', receiving_node)
        citation_div.setAttribute('id', 'article-citation')
        self.appendNewElementWithText('b', 'Citation: ', citation_div)
        self.appendNewText(citation_text, citation_div)

    def make_article_info_editors(self, editors, body):
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
                name = editor.name[0].surname
                if editor.name[0].given:
                    name = editor.name[0].given + ' ' + name
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
                    addr = refer_aff.getElementsByTagName('addr-line')
                    if addr:
                        editors_div.childNodes += addr[0].childNodes
                    else:
                        editors_div.childNodes += refer_aff.childNodes

    def make_article_info_dates(self, body):
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
            self.appendNewText(self.format_date_string(received) + ' ', dates_div)

        #Accepted - Optional
        accepted = self.metadata.history['accepted']
        if accepted:
            self.appendNewElementWithText('b', 'Accepted: ', dates_div)
            self.appendNewText(self.format_date_string(accepted) + ' ', dates_div)

        #Published - Required
        published = self.metadata.pub_date['epub']
        self.appendNewElementWithText('b', 'Published: ', dates_div)
        self.appendNewText(self.format_date_string(published), dates_div)

    def make_article_info_copyright(self, body):
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
        self.appendNewElementWithText('b', 'Copyright: ', copyright_div)

        #Construct the string for the copyright statement
        copyright_string = u' \u00A9 '
        #I expect year to always be there
        copyright_string += utils.nodeText(permissions.year) + ' '
        #Holder won't always be there
        if permissions.holder:
            try:
                copyright_string += utils.nodeText(permissions.holder) + '.'
            except AttributeError:  # Some articles have empty <copyright-holder>s
                pass
        #I don't know if the license will always be included
        if permissions.license:  # I hope this is a general solution
            license_p = self.getChildrenByTagName('license-p', permissions.license)[0]
            copyright_string += ' ' + utils.nodeText(license_p)
        self.appendNewText(copyright_string, copyright_div)

    def make_article_info_funding(self, body):
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

    def make_article_info_competing_interests(self, body):
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

    def make_article_info_correspondences(self, body):
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

    def make_article_info_footnotes_other(self, body):
        """
        This will catch all of the footnotes of type 'other' in the <fn-group>
        of the <back> element.
        """
        #Check for backmatter, skip if it doesn't exist
        if not self.backmatter:
            return
        #Check for backmatter fn-groups, skip if empty
        fn_groups = self.backmatter.fn_group
        if not fn_groups:
            return
        #Look for fn nodes of fn-type 'other'
        other_fns = []
        for fn_group in fn_groups:
            for fn in self.getChildrenByTagName('fn', fn_group):
                if fn.getAttribute('fn-type') == 'other':
                    other_fns.append(fn)
        if other_fns:
            other_fn_div = self.appendNewElement('div', body)
            other_fn_div.setAttribute('id', 'back-fn-other')
        for other_fn in other_fns:
            other_fn_div.childNodes += other_fn.childNodes

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

    def convert_fig_elements(self, body):
        """
        Responsible for the correct conversion of JPTS 3.0 <fig> elements to
        OPS xhtml. Aside from translating <fig> to <img>, the content model
        must be edited.
        """
        for fig in body.getElementsByTagName('fig'):
            if fig.parentNode.tagName == 'p':
                self.elevateNode(fig)
        figs = body.getElementsByTagName('fig')
        for fig in figs:
            #self.convert_fn_elements(fig)
            #self.convert_disp_formula_elements(fig)
            #Parse all fig attributes to a dict
            fig_attributes = self.getAllAttributes(fig, remove=False)
            #Determine if there is a <label>, 0 or 1, grab the node
            try:
                label_node = self.getChildrenByTagName('label', fig)[0]
            except IndexError:  # No label tag
                label_node = None
            #Determine if there is a <caption>, grab the node
            try:
                caption_node = self.getChildrenByTagName('caption', fig)[0]
            except IndexError:
                caption_node = None

            #Get the graphic node in the fig, treat as mandatory
            graphic_node = self.getChildrenByTagName('graphic', fig)[0]
            #Create a file reference for the image
            graphic_xlink_href = graphic_node.getAttribute('xlink:href')
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_frag
            img_path = '/'.join([img_dir, file_name])

            #Create OPS content, using image path, label, and caption
            fig_parent = fig.parentNode
            #Create a horizontal rule
            fig_parent.insertBefore(self.doc.createElement('hr'), fig)
            #Create the img element
            img_element = self.doc.createElement('img')
            img_element.setAttribute('alt', 'A Figure')
            img_element.setAttribute('id', fig_attributes['id'])
            img_element.setAttribute('src', img_path)
            #Insert the img element
            fig_parent.insertBefore(img_element, fig)

            #Create content for the label and caption
            if caption_node or label_node:  # These will go into a <div> after <img>
                img_caption_div = self.doc.createElement('div')
                img_caption_div.setAttribute('class', 'figure-caption')
                img_caption_div_b = self.appendNewElement('b', img_caption_div)
                if label_node:
                    img_caption_div_b.childNodes += label_node.childNodes
                    self.appendNewText('. ', img_caption_div_b)
                #The caption element may have <title> 0 or 1, and <p> 0 or more
                if caption_node:
                    #Detect caption title
                    caption_title = self.getChildrenByTagName('title', caption_node)
                    if caption_title:
                        img_caption_div_b.childNodes += caption_title[0].childNodes
                        self.appendNewText(' ', img_caption_div_b)
                    #Detect <p>s
                    caption_ps = self.getChildrenByTagName('p', caption_node)
                    for each_p in caption_ps:
                        img_caption_div.childNodes += each_p.childNodes
                #Now that we have created the img caption div content, insert
                fig_parent.insertBefore(img_caption_div, fig)

            #Create a horizontal rule
            fig_parent.insertBefore(self.doc.createElement('hr'), fig)

            #Remove the original <fig>
            fig_parent.removeChild(fig)

    def convert_table_wrap_elements(self, body):
        """
        Responsible for the correct conversion of JPTS 3.0 <table-wrap>
        elements to OPS content.
        """
        table_wraps = body.getElementsByTagName('table-wrap')
        for tab in table_wraps:
            #Parse all attributes to a dict
            tab_attributes = self.getAllAttributes(tab, remove=False)
            #Determine if there is a <label>, 0 or 1, grab the node
            #label_text is for serialized text for the tabled version
            try:
                label_node = self.getChildrenByTagName('label', tab)[0]
            except IndexError:  # No label tag
                label_node = None
                label_text = ''
            else:
                label_text = utils.serializeText(label_node, stringlist=[])
            #Determine if there is a <caption>, grab the node
            try:
                caption_node = self.getChildrenByTagName('caption', tab)[0]
            except IndexError:
                caption_node = None

            #Get the alternatives node, for some articles it will hold the graphic
            #The graphic is mandatory
            alternatives = self.getChildrenByTagName('alternatives', tab)
            if alternatives:  # New articles are this way
                graphic_node = self.getChildrenByTagName('graphic', alternatives[0])[0]
                table_node = self.getChildrenByTagName('table', alternatives[0])[0]
            else:  # Old articles seem to be this way
                graphic_node = self.getChildrenByTagName('graphic', tab)[0]
                #TODO: Find some way to properly render out the HTML comments
                table_node = False
            #Label and move the html table node to the list of html tables
            if table_node:
                table_node.setAttribute('id', tab_attributes['id'])
                table_node.setAttribute('label', label_text)
                self.html_tables.append(table_node)
                try:
                    foot = self.getChildrenByTagName('table-wrap-foot', tab)[0]
                except IndexError:
                    pass
                else:
                    self.html_tables.append(foot)

            #Create a file reference for the image
            graphic_xlink_href = graphic_node.getAttribute('xlink:href')
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_frag
            img_path = '/'.join([img_dir, file_name])

            #Create OPS content, using image path, label, and caption
            tab_parent = tab.parentNode
            #Create a horizontal rule
            tab_parent.insertBefore(self.doc.createElement('hr'), tab)
            #Create the img element
            img_element = self.doc.createElement('img')
            img_element.setAttribute('alt', 'A Table')
            img_element.setAttribute('id', tab_attributes['id'])
            img_element.setAttribute('src', img_path)

            #Create content for the label and caption
            if caption_node or label_node:  # These will go into a <div> before <img>
                img_caption_div = self.doc.createElement('div')
                img_caption_div.setAttribute('class', 'table-caption')
                img_caption_div_b = self.appendNewElement('b', img_caption_div)
                if label_node:
                    img_caption_div_b.childNodes += label_node.childNodes
                    self.appendNewText('. ', img_caption_div_b)
                #The caption element may have <title> 0 or 1, and <p> 0 or more
                if caption_node:
                    #Detect caption title
                    caption_title = self.getChildrenByTagName('title', caption_node)
                    if caption_title:
                        img_caption_div.childNodes += caption_title[0].childNodes
                        self.appendNewText(' ', img_caption_div)
                    #Detect <p>s
                    caption_ps = self.getChildrenByTagName('p', caption_node)
                    for each_p in caption_ps:
                        img_caption_div.childNodes += each_p.childNodes
                #Now that we have created the img caption div content, insert
                tab_parent.insertBefore(img_caption_div, tab)

            #Insert the img element
            tab_parent.insertBefore(img_element, tab)

            #Create a link to the html version of the table
            if table_node:
                html_table_link = self.doc.createElement('a')
                html_table_link.setAttribute('href', self.tab_frag.format(tab_attributes['id']))
                self.appendNewText('HTML version of this table', html_table_link)
                tab_parent.insertBefore(html_table_link, tab)

            #Create a horizontal rule
            tab_parent.insertBefore(self.doc.createElement('hr'), tab)

            #Remove the original <table-wrap>
            tab_parent.removeChild(tab)

    def convert_sec_elements(self, body):
        """
        Convert <sec> elements to <div> elements and handle ids and attributes
        """
        #Find all <sec> in body
        sec_elements = body.getElementsByTagName('sec')
        count = 0
        #Convert the sec elements
        for sec in sec_elements:
            sec.tagName = 'div'
            self.renameAttributes(sec, [('sec-type', 'class')])
            if not sec.getAttribute('id'):  # Give it am id if it is missing
                sec.setAttribute('id', 'OA-EPUB-{0}'.format(str(count)))
                count += 1

    def convert_div_titles(self, node, depth=0):
        """
        A recursive function to convert <title> nodes directly beneath <div>
        nodes into appropriate OPS compatible header tags.
        """
        depth_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
        #Look for divs
        for div in self.getChildrenByTagName('div', node):
            #Look for a label
            try:
                div_label = self.getChildrenByTagName('label', div)[0]
            except IndexError:
                div_label_text = ''
            else:
                if not div_label.childNodes:
                    div.removeChild(div_label)
                else:
                    div_label_text = utils.nodeText(div_label)
                    div.removeChild(div_label)
            #Look for a title
            try:
                div_title = self.getChildrenByTagName('title', div)[0]
            except IndexError:
                div_title = None
            else:
                if not div_title.childNodes:
                    div.removeChild(div_title)
                else:
                    div_title.tagName = depth_tags[depth]
                    if div_label_text:
                        label_node = self.doc.createTextNode(div_label_text)
                        div_title.insertBefore(label_node, div_title.firstChild)
            self.convert_div_titles(div, depth=depth + 1)

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
                   u'aff': self.main_frag,
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

    def convert_disp_formula_elements(self, body):
        """
        <disp-formula> elements must be converted to OPS conforming elements
        """
        disp_formulas = body.getElementsByTagName('disp-formula')
        for disp in disp_formulas:
            #Parse all fig attributes to a dict
            disp_attributes = self.getAllAttributes(disp, remove=False)
            #Determine if there is a <label>, 0 or 1, grab_node
            try:
                label_node = self.getChildrenByTagName('label', disp)[0]
            except IndexError:  # No label tag
                label_node = None

            #Get the graphic node in the fig, treat as mandatory
            graphic_node = self.getChildrenByTagName('graphic', disp)[0]
            #Create a file reference for the image
            graphic_xlink_href = graphic_node.getAttribute('xlink:href')
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_frag
            img_path = '/'.join([img_dir, file_name])

            #Create OPS content, using image path, and label
            disp_parent = disp.parentNode

            #Create the img element
            img_element = self.doc.createElement('img')
            img_element.setAttribute('alt', 'A Display Formula')
            img_element.setAttribute('id', disp_attributes['id'])
            img_element.setAttribute('class', 'disp-formula')
            img_element.setAttribute('src', img_path)

            #Insert the img element
            disp_parent.insertBefore(img_element, disp)
            #Create content for the label
            if label_node:
                disp_parent.insertBefore(label_node, img_element)
                label_node.tagName = 'b'

            #Remove the old disp-formula element
            disp_parent.removeChild(disp)

    def convert_inline_formula_elements(self, body):
        """
        <inline-formula> elements must be converted to OPS conforming elements

        These elements may contain <inline-graphic> elements, textual content,
        or both.
        """
        for inline in body.getElementsByTagName('inline-formula'):
            #Grab all the attributes of the formula element
            inline_attributes = self.getAllAttributes(inline, remove=True)
            #Convert the inline-formula element to a div and give it a class
            inline.tagName = 'span'
            inline.setAttribute('class', 'inline-formula')
            #Determine if there is an <inline-graphic>
            try:
                inline_graphic = self.getChildrenByTagName('inline-graphic', inline)[0]
            except IndexError:
                inline_graphic = None
            else:
                #Convert the inline-graphic element to an img element
                inline_graphic.tagName = 'img'
                #Get all of the attributes, with removal on
                inline_graphic_attributes = self.getAllAttributes(inline_graphic, remove=True)
                #Create a file reference for the image using the xlink:href attribute value
                graphic_xlink_href = inline_graphic_attributes['xlink:href']
                file_name = graphic_xlink_href.split('.')[-1] + '.png'
                img_dir = 'images-' + self.doi_frag
                img_path = '/'.join([img_dir, file_name])
                #Set the source to the image path
                inline_graphic.setAttribute('src', img_path)
                #Give it an inline-formula class
                inline_graphic.setAttribute('class', 'disp-formula')
                #Alt text
                inline_graphic.setAttribute('alt', 'An Inline Formula')


    def convert_named_content_elements(self, body):
        """
        <named-content> elements are used by PLoS for certain spcecial kinds
        of content, such as genus-species denotations. This method will convert
        the tagname to <span> and the content-type attribute to class. I expect
        that this will provide an easily extensible basis for CSS handling.
        """
        for named_content in body.getElementsByTagName('named-content'):
            named_content.tagName = 'span'
            attrs = self.getAllAttributes(named_content, remove=True)
            if 'content-type' in attrs:
                named_content.setAttribute('class', attrs['content-type'])

    def convert_disp_quote_elements(self, body):
        """
        Extract or extended quoted passage from another work, usually made
        typographically distinct from surrounding text

        <disp-quote> elements have a relatively complex content model, but it
        appears that PLoS typically employs a simple <p> child element to hold
        all of the text, until otherwise found, this method handles the
        conversion under this assumption.
        """
        for disp_quote in body.getElementsByTagName('disp-quote'):
            disp_quote_parent = disp_quote.parentNode
            if disp_quote_parent.tagName == 'p':
                grandparent = disp_quote_parent.parentNode
                self.elevateNode(disp_quote)
                if not disp_quote_parent.childNodes:
                    grandparent.removeChild(disp_quote_parent)
                #The grandparent is now the new parent
                disp_quote_parent = grandparent
            paragraph = self.getChildrenByTagName('p', disp_quote)[0]
            top_hr = self.doc.createElement('hr')
            bottom_hr = self.doc.createElement('hr')
            for element in [top_hr, paragraph, bottom_hr]:
                element.setAttribute('class', 'disp-quote')
                disp_quote_parent.insertBefore(element, disp_quote)
            disp_quote_parent.removeChild(disp_quote)
            

    def convert_boxed_text_elements(self, body):
        """
        Textual material that is part of the body of text but outside the
        flow of the narrative text, for example, a sidebar, marginalia, text
        insert (whether enclosed in a box or not), caution, tip, note box, etc.

        <boxed-text> elements for PLoS appear to all contain a single <sec>
        element which frequently contains a <title> and various other content.
        This method will elevate the <sec> element, adding class information as
        well as processing the title.
        """
        for boxed_text in body.getElementsByTagName('boxed-text'):
            boxed_text_attrs = self.getAllAttributes(boxed_text, remove=False)
            boxed_text_parent = boxed_text.parentNode
            sec = self.getChildrenByTagName('sec', boxed_text)[0]
            title = self.getChildrenByTagName('title', sec)
            top_hr = self.doc.createElement('hr')
            bottom_hr = self.doc.createElement('hr')
            if title:
                title[0].tagName = 'b'
            sec.tagName = 'div'
            sec.setAttribute('class', 'boxed-text')
            sec.setAttribute('id', boxed_text_attrs['id'])
            boxed_text_parent.insertBefore(sec, boxed_text)
            boxed_text_parent.removeChild(boxed_text)

    def convert_supplementary_material_elements(self, body):
        """
        Supplementary material are not, nor are they generally expected to be,
        packaged into the epub file. Though this is a technical possibility,
        and certain epub reading systems (such as those run on a PC) might be
        reasonably able to handle the external handling of diverse file formats
        I presume that supplementary material will remain separate from the
        document. So special cases aside, external links to supplementary
        material will be employed; this will require internet connection for
        access.

        As for content in <supplementary-material>, they appear to strictly
        contain 1 <label> element, followed by a <caption><title><p></caption>
        substructure.
        """
        for supplementary in body.getElementsByTagName('supplementary-material'):
            transfer_id = False
            attributes = self.getAllAttributes(supplementary, remove=False)
            supplementary_parent = supplementary.parentNode
            labels = self.getChildrenByTagName('label', supplementary)
            resource_url = utils.plos_fetch_single_representation(self.doi_frag, attributes['xlink:href'])
            if labels:
                label = labels[0]
                label.tagName = 'a'
                label.setAttribute('href', resource_url)
                label.setAttribute('id', attributes['id'])
                self.appendNewText('. ', label)
                transfer_id = True
                supplementary_parent.insertBefore(label, supplementary)
            caption = self.getChildrenByTagName('caption', supplementary)
            if caption:
                titles = self.getChildrenByTagName('title', caption[0])
                paragraphs = self.getChildrenByTagName('p', caption[0])
                if titles:
                    title = titles[0]
                    title.tagName = 'b'
                    if not transfer_id:
                        title.setAttribute('id', attributes['id'])
                    supplementary_parent.insertBefore(title, supplementary)
                if paragraphs:
                    paragraph = paragraphs[0]
                    if not transfer_id:
                        paragraph.setAttribute('id', attributes['id'])
                    supplementary_parent.insertBefore(paragraph, supplementary)
            supplementary_parent.removeChild(supplementary)

    def convert_verse_group_elements(self, body):
        """
        A song, poem, or verse

        Implementor’s Note: No attempt has been made to retain the look or
        visual form of the original poetry.

        This unusual element, <verse-group> is used to convey poetry and is
        recursive in nature (it may contain further <verse-group> elements).
        Examples of these tags are sparse, so it remains difficult to ensure
        full implementation. This method will attempt to handle the label,
        title, and subtitle elements correctly, while converting <verse-lines>
        to italicized lines.
        """
        for verse_group in body.getElementsByTagName('verse-group'):
            label = self.getChildrenByTagName('label', verse_group)
            title = self.getChildrenByTagName('title', verse_group)
            subtitle = self.getChildrenByTagName('subtitle', verse_group)
            verse_group.tagName = 'div'
            verse_group.setAttribute('id', 'verse-group')
            if any([label, title, subtitle]):
                new_verse_title = self.doc.createElement('b')
                verse_group.insertBefore(verse_group.firstChild)
                if label:
                    new_verse_title.childNodes += label[0].childNodes
                if title:
                    new_verse_title.childNodes += title[0].childNodes
                if subtitle:
                    new_verse_title.childNodes += subtitle[0].childNodes
            for verse_line in self.getChildrenByTagName('verse-line', verse_group):
                verse_line.tagName = 'p'
                verse_line.setAttribute('class', 'verse-line')

    def convert_fn_elements(self, body):
        """
        <fn> elements may be used in the main text body outside of tables and
        figures for purposes such as erratum notes. It appears that PLoS
        practice is to not show erratum notes in the web or pdf formats after
        the appropriate corrections have been made to the text. The erratum
        notes are thus the only record that an error was made.

        This method will attempt to display footnotes unless the note can be
        identified as an Erratum, in which case it will be removed in
        accordance with PLoS' apparent guidelines.
        """
        footnotes = body.getElementsByTagName('fn')
        for footnote in footnotes:
            #Get the attributes
            attributes = self.getAllAttributes(footnote, remove=False)
            footnote_parent = footnote.parentNode
            #Find the footnoteparagraph
            footnote_paragraphs = self.getChildrenByTagName('p', footnote)
            if footnote_paragraphs:  # A footnote paragraph exists
                #Grab the first, and only, paragraph
                paragraph = footnote_paragraphs[0]
                #Graph the paragraph text
                paragraph_text = utils.serializeText(paragraph, stringlist=[])
                #See if it is a corrected erratum
                corrected_erratum = False
                if paragraph_text.startswith('Erratum') and 'Corrected' in paragraph_text:
                    corrected_erratum = True
                #Now remove the footnote if it is a corrected erratum
                if corrected_erratum:
                    footnote_parent.removeChild(footnote)
                    continue  # Move on to the next footnote

                #Process the footnote paragraph if it is not a corrected erratum
                if 'id' in attributes:
                    paragraph.setAttribute('id', attributes['id'])
                if 'fn-type' in attributes:
                    paragraph_class = 'fn-type-{0}'.format(attributes['fn-type'])
                    paragraph.setAttribute('class', paragraph_class)
                else:
                    paragraph.setAttribute('class', 'fn')
                footnote_parent.insertBefore(paragraph, footnote)
                footnote_parent.removeChild(footnote)

            else:  # A footnote paragraph does not exist
                footnote_parent.removeChild(footnote)

    def convert_list_elements(self, body):
        """
        A sequence of two or more items, which may or may not be ordered.

        The <list> element has an optional <label> element and optional <title>
        element, followed by one or more <list-item> elements. This is element
        is recursive as the <list-item> elements may contain further <list> or
        <def-list> elements. Much of the potential complexity in dealing with
        lists comes from this recursion.

        This element has the list-type attribute which has the following
        suggested values:

        order -  Ordered list. Prefix character is a number or a letter,
            depending on style.
        bullet - Unordered or bulleted list. Prefix character is a bullet,
            dash, or other symbol.
        alpha-lower - Ordered list. Prefix character is a lowercase
            alphabetical character.
        alpha-upper - Ordered list. Prefix character is an uppercase
            alphabetical character.
        roman-lower - Ordered list. Prefix character is a lowercase roman
            numeral.
        roman-upper - Ordered list. Prefix character is an uppercase roman
            numeral.
        simple - Simple or plain list (No prefix character before each item)

        Prefix-words are not properly supported at this time due to the
        impracticality in EPUB2. Perhaps in the future, or in EPUB3.
        The code provides a notice of the improperly handled prefix-word, and
        manual review should be employed.
        """
        #I have yet to gather many examples of this element, and may have to
        #write a recursive method for the processing of lists depending on how
        #PLoS produces their XML, for now this method is ignorant of nesting

        #TODO: prefix-words, one possible solution would be to have this method
        #edit the CSS to provide formatting support for arbitrary prefixes...

        #list_el is used instead of list (list is reserved)
        for list_el in body.getElementsByTagName('list'):
            list_el_attributes = self.getAllAttributes(list_el, remove=True)
            list_el_parent = list_el.parentNode
            list_el_type = list_el_attributes['list-type']
            #Unordered list if '', 'bullet', or 'simple'
            if list_el_type in ['', 'bullet', 'simple']:
                list_el.tagName = 'ul'
                #'' and 'bullet' are treated as the same default case
                #If the unordered list is simple, we wish to suppress bullets
                if list_el_type == 'simple':  # Use CSS to suppress
                    list_el.setAttribute('class', 'simple')
            #Ordered list if otherwise
            else:
                list_el.tagName = 'ol'
                list_el.setAttribute('class', list_el_type)
            #Pass on the id if it exists
            if 'id' in list_el_attributes:
                list_el.setAttribute('id', list_el_attributes['id'])
            #Convert the <list-item> element tags to 'li'
            for list_item in self.getChildrenByTagName('list-item', list_el):
                list_item.tagName = 'li'

    def convert_def_list_elements(self, body):
        """
        A list in which each item consists of two parts: a word, phrase, term,
        graphic, chemical structure, or equation paired with one of more
        descriptions, discussions, explanations, or definitions of it.

        <def-list> elements are lists of <def-item> elements which are in turn
        composed of a pair of term (<term>) and definition (<def>). This method
        will convert the <def-list> to a classed <div> with a styled format
        for the terms and definitions.
        """
        for def_list in body.getElementsByTagName('def-list'):
            def_list_attributes = self.getAllAttributes(def_list, remove=True)
            def_list.tagName = 'div'
            def_list.setAttribute('class', 'def-list')
            if 'id' in def_list_attributes:
                def_list.setAttribute('id', def_list_attributes['id'])
            def_item_list = self.getChildrenByTagName('def-item', def_list)
            for def_item in def_item_list:
                term = self.getChildrenByTagName('term', def_item)[0]
                term.tagName = 'p'
                term.setAttribute('class', 'def-item-term')
                def_list.insertBefore(term, def_item)
                definition = self.getChildrenByTagName('def', def_item)[0]
                def_para = self.getChildrenByTagName('p', definition)[0]
                definition.childNodes += def_para.childNodes
                definition.removeChild(def_para)
                definition.tagName = 'p'
                definition.setAttribute('class', 'def-item-def')
                def_list.insertBefore(definition, def_item)
                def_list.removeChild(def_item)

    def convert_ref_list_elements(self, body):
        """
        List of references (citations) for an article, which is often called
        “References”, “Bibliography”, or “Additional Reading”.

        No distinction is made between lists of cited references and lists of
        suggested references.

        This method should not be confused with the method(s) employed for the
        formatting of a proper bibliography, though they are related.
        Similarly, this is an area of major openness in development, I lack
        access to PLOS' algorithm for proper citation formatting.
        """
        #TODO: DOES NOT FUNCTION AS INTENDED; make a proper one someday
        for ref_list in body.getElementsByTagName('ref-list'):
            ref_list_attributes = self.getAllAttributes(ref_list, remove=True)
            ref_list.tagName = 'div'
            ref_list.setAttribute('class', 'ref-list')
            try:
                label = self.getChildrenByTagName('label', ref_list)[0]
            except IndexError:
                pass
            else:
                label.tagName = 'h3'
            for ref in self.getChildrenByTagName('ref', ref_list):
                ref_text = utils.serializeText(ref, stringlist=[])
                ref_list_p = self.appendNewElementWithText('p', ref_text, ref_list)
                ref_list.removeChild(ref)

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSPLoS')
