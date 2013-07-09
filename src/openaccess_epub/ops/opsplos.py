# -*- coding: utf-8 -*-
"""
This module defines an OPS content generator class for PLoS. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
from .opsmeta import OPSMeta
from lxml import etree
from copy import copy, deepcopy
import os
import sys
import logging

log = logging.getLogger('OPSPLoS')


class OPSPLoS(OPSMeta):
    """
    This provides the full feature set to create OPS content for an ePub file
    from a PLoS journal article.
    """
    def __init__(self, article, output_dir):
        OPSMeta.__init__(self, article)
        log.info('Initiating OPSPLoS')
        #Set some initial hooks into the input article content
        self.article = article
        self.metadata = article.metadata
        self.doi = article.get_DOI()
        #From "10.1371/journal.pone.0035956" get "journal.pone.0335956"
        self.doi_frag = self.doi.split('10.1371/')[1]
        self.make_fragment_identifiers()
        self.ops_dir = os.path.join(output_dir, 'OPS')
        self.html_tables = []
        self.main_body = self.create_main()
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
        #The first job is to create a file copy the article body to it
        self.document = self.make_document('main')
        if self.article.body is not None:
            self.document.getroot().append(deepcopy(self.article.body))
        else:
            return None  # TODO: Backmatter handling without body
        body = self.document.getroot().find('body')

        #The section that contains the Article Title, List of Authors and
        #Affiliations, and Abstracts is referred to as the Heading
        self.make_heading(body)

        #The ArticleInfo section contains the (self) Citation, Editors, Dates,
        #Copyright, Funding Statement, Competing Interests Statement,
        #Correspondence, and Footnotes. Maybe more...
        self.make_article_info(body)

        #The Back Section of an article may contain important information aside
        #from the Bibliography. Unlike the Body, this method will look for
        #supported elements and add them appropriately to the XML
        self.make_back_matter(body)

        #Handle node conversion
        self.convert_disp_formula_elements(body)
        self.convert_inline_formula_elements(body)
        self.convert_disp_quote_elements(body)
        self.convert_boxed_text_elements(body)
        self.convert_verse_group_elements(body)
        self.convert_supplementary_material_elements(body)
        self.convert_fn_elements(body)
        self.convert_def_list_elements(body)
        self.convert_ref_list_elements(body)
        self.convert_list_elements(body)

        self.convert_fig_elements(body)
        self.convert_table_wrap_elements(body)

        self.convert_graphic_elements(body)

        #TODO: Back matter stuffs

        #These come last for a reason
        self.convert_sec_elements(body)
        self.convert_div_titles(body)
        self.post_processing_conversion(body)

        #Finally, write to a document
        self.write_document(os.path.join(self.ops_dir, self.main_frag[:-4]), self.document)

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
        #heading_div = etree.SubElement(receiving_node, 'div')
        heading_div = etree.Element('div')
        receiving_node.insert(0, heading_div)
        heading_div.attrib['id'] = 'Heading'
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
        article_info_div = etree.Element('div', {'id': 'ArticleInfo'})
        receiving_node.insert(1, article_info_div)
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

    def post_processing_conversion(self, top):
        """
        This is a top-level function for calling a suite of methods which
        translate JPTS 3.0 XML to OPS XML for PLoS content.

        These methods will search the element tree beneath the specified top
        element node, finding the elements at any depth in order to coerce them
        to OPS-suitable elements. This should be called as a final step, to
        operate on all such elements in the final product.
        """
        #TODO: Review this function for completion
        self.convert_JPTS_emphasis(top)
        self.convert_address_linking_elements(top)
        self.convert_xref_elements(top)
        self.convert_named_content_elements(top)
        self.convert_sec_elements(top)
        self.convert_div_titles(top, depth=1)

    def create_biblio(self):
        """
        This method encapsulates the functions necessary to create the biblio
        segment of the article.
        """
        self.document = self.make_document('biblio')
        body = etree.SubElement(self.document.getroot(), 'body')
        body.attrib['id'] = 'references'
        if self.article.metadata.back is None:
            return
        else:
            refs = self.metadata.back.node.findall('.//ref')
        if len(refs) == 0:
            return
        for ref in refs:
            ref_p = etree.SubElement(body, 'p')
            ref_p.attrib['id'] = ref.attrib['id']
            ref_p.text = str(etree.tostring(ref, method='text', encoding='utf-8'), encoding='utf-8')

        self.write_document(os.path.join(self.ops_dir, self.bib_frag[:-4]), self.document)

    def create_tables(self):
        """
        This method encapsulates the functions necessary to create a file
        containing html versions of all the tables in the article. If there
        are no tables, the file is not created.
        """

        self.document = self.make_document('tables')
        body = etree.SubElement(self.document.getroot(), 'body')
        body.attrib['id'] = 'references'

        for table in self.html_tables:
            if table.tag == 'table-wrap-foot':
                foot_div = etree.SubElement(body, 'div')
                foot_div.attrib['class'] = 'table-wrap-foot'
                element_methods.append_all_below(body, table)
                continue
            #Use the custom created label attribute to pass table heading to the tables file
            if 'label' in table.attrib:
                #Take the label value and remove the attribute
                label = table.attrib.pop('label')
                label_div = etree.SubElement(body, 'div')
                label_div_b = etree.SubElement(label_div, 'b')
                label_div_b.text = label
            #Move the table to the body
            body.append(table)
            #Move all divs under the table to the body
            for div in table.findall('.//div'):
                body.append(div)

        #Handle node conversion
        self.convert_emphasis_elements(body)
        self.convert_fn_elements(body)
        self.convert_disp_formula_elements(body)
        self.convert_inline_formula_elements(body)
        self.convert_xref_elements(body)

        #Finally, write to a document
        self.write_document(os.path.join(self.ops_dir, self.tab_frag[:-4]), self.document)

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
        authors_list = []
        for contrib_group in self.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if contrib.attrs['contrib-type'] == 'author':
                    authors_list.append(contrib)
        return authors_list

    def get_editors_list(self):
        """
        Gets a list of all editors described in the metadata.
        """
        editors_list = []
        for contrib_group in self.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if contrib.attrs['contrib-type'] == 'editor':
                    editors_list.append(contrib)
        return editors_list

    def make_heading_title(self, receiving_element):
        """
        Makes the Article Title for the Heading.

        Metadata element, content derived from FrontMatter
        """
        article_title = deepcopy(self.metadata.front.article_meta.title_group.article_title.node)
        article_title.tag = 'h1'
        article_title.attrib['id'] = 'title'
        article_title.attrib['class'] = 'article-title'
        receiving_element.append(article_title)

    def make_heading_authors(self, authors, receiving_node):
        """
        Constructs the Authors content for the Heading. This should display
        directly after the Article Title.

        Metadata element, content derived from FrontMatter
        """
        #Make and append a new element to the passed receiving_node
        author_element = etree.SubElement(receiving_node, 'h3', {'class': 'authors'})
        #Construct content for the author element
        first = True
        for author in authors:
            if first:
                first = False
            else:
                element_methods.append_new_text(author_element, ',', join_str='')
            if len(author.collab) > 0:  # If collab, just add rich content
                #Assume only one collab
                element_methods.append_all_below(author_element, author.collab[0].node)
            elif len(author.anonymous) > 0:  # If anonymous, just add "Anonymous"
                element_methods.append_new_text(author_element, 'Anonymous')
            else:  # Author is neither Anonymous or a Collaboration
                name = author.name[0]  # Work with only first name listed
                surname = name.surname.text
                if name.given_names is not None:
                    name_text = ' '.join([name.given_names.text, surname])
                else:
                    name_text = surname
                element_methods.append_new_text(author_element, name_text)
            #TODO: Handle author footnote references, also put footnotes in the ArticleInfo
            #Example: journal.pbio.0040370.xml
            for xref in author.xref:
                if xref.attrs['ref-type'] in ['corresp', 'aff']:
                    try:
                        sup_element = xref.sup[0].node
                    except IndexError:
                        sup_text = ''
                    else:
                        sup_text = element_methods.all_text(sup_element)
                    new_sup = etree.SubElement(author_element, 'sup')
                    new_sup.text = sup_text
                    sup_link = etree.SubElement(new_sup, 'a')
                    sup_link.attrib['href'] = self.main_frag.format(xref.attrs['rid'])

    def make_heading_affiliations(self, receiving_node):
        """
        Makes the content for the Author Affiliations, displays after the
        Authors segment in the Heading.

        Metadata element, content derived from FrontMatter
        """
        #Get all of the aff element tuples from the metadata
        affs = self.metadata.front.article_meta.aff
        #Create a list of all those pertaining to the authors
        author_affs = [i for i in affs if 'aff' in i.attrs['id']]
        #Count them, used for formatting
        author_aff_count = len(self.metadata.front.article_meta.aff)
        if author_aff_count > 0:
            affs_div = etree.SubElement(receiving_node, 'div', {'id': 'affiliations'})

        #A simple way that seems to work by PLoS convention, but does not treat
        #the full scope of the <aff> element
        for aff in author_affs:
            #Expecting id to always be present
            aff_id = aff.attrs['id']
            #Create a span element to accept extracted content
            aff_span = etree.SubElement(affs_div, 'span')
            aff_span.attrib['id'] = aff_id
            #Get the first label node and the first addr-line node
            if len(aff.label) > 0:
                label = aff.label[0].node
                label_text = element_methods.all_text(label)
                bold = etree.SubElement(aff_span, 'b')
                bold.text = label_text+' '
            if len(aff.addr_line) > 0:
                addr_line = aff.addr_line[0].node
                element_methods.append_new_text(aff_span, element_methods.all_text(addr_line))
            else:
                element_methods.append_new_text(aff_span, element_methods.all_text(aff))
            if author_affs.index(aff) < author_aff_count-1:
                element_methods.append_new_text(aff_span, ', ', join_str='')

    def make_heading_abstracts(self, receiving_node):
        """
        An article may contain data for various kinds of abstracts. This method
        works on those that are included in the Heading. This is displayed
        after the Authors and Affiliations.

        Metadata element, content derived from FrontMatter
        """
        for abstract in self.metadata.front.article_meta.abstract:
            #Make a copy of the abstract
            abstract_copy = deepcopy(abstract.node)
            #Remove title elements in the abstracts
            #TODO: Fix this removal, this is not always appropriate
            for title in abstract_copy.findall('.//title'):
                title.getparent().remove(title)
            #Create a header for the abstract
            abstract_header = etree.Element('h2')
            #Rename the abstract tag
            abstract_copy.tag = 'div'
            #Remove all of the attributes from the abstract copy top element
            element_methods.remove_all_attributes(abstract_copy)
            #Set the header text and abstract id according to abstract type
            abstract_type = abstract.attrs['abstract-type']
            if abstract_type == 'summary':  # Should be an Author Summary
                abstract_header.text = 'Author Summary'
                abstract_copy.attrib['id'] = 'author-summary'
            elif abstract_type == 'editors-summary': # Should be an Editor Summary
                abstract_header.text = 'Editors\' Summary'
                abstract_copy.attrib['id'] = 'editor-summary'
            elif abstract_type is None:  # The attribute was missing, implying main
                abstract_header.text = 'Abstract'
                abstract_copy.attrib['id'] = 'abstract'
            elif abstract_type == 'toc':
                continue
            else:
                abstract_header.text = 'Unhandled value for abstract-type {0}'.format(abstract_type)
                abstract_copy.attrib['id'] = abstract_type
            receiving_node.append(abstract_header)
            receiving_node.append(abstract_copy)

    def make_article_info_citation(self, receiving_el):
        """
        Creates a self citation node for the ArticleInfo of the article.

        This method relies on self.format_self_citation() as an implementation
        of converting an article's metadata to a plain string, and then adds
        composes content for the display of that string in the ArticleInfo.
        """
        citation_text = self.format_self_citation()
        citation_div = etree.SubElement(receiving_el, 'div')
        citation_div.attrib['id'] = 'article-citation'
        b = etree.SubElement(citation_div, 'b')
        b.text = 'Citation: {0}'.format(citation_text)

    def make_article_info_editors(self, editors, receiving_el):
        if not editors:  # No editors
            return

        editors_div = etree.SubElement(receiving_el, 'div')
        editor_bold = etree.SubElement(editors_div, 'b')
        if len(editors) > 1:  # Pluralize if more than one editor
            editor_bold.text = 'Editors: '
        else:
            editor_bold.text = 'Editor: '
        first = True
        for editor in editors:
            if first:
                first = False
            else:
                element_methods.append_new_text(editors_div, '; ', join_str='')
            
            if len(editor.anonymous) > 0:
                element_methods.append_new_text(editors_div, 'Anonymous', join_str='')
            elif len(editor.collab) > 0:
                element_methods.append_all_below(editors_div, editor.collab[0].node)
            else:
                name = editor.name[0]  # Work with only first name listed
                surname = name.surname.text
                if name.given_names is not None:
                    name_text = ' '.join([name.given_names.text, surname])
                else:
                    name_text = surname
                element_methods.append_new_text(editors_div, name_text)

            for xref in editor.xref:
                if xref.attrs['ref-type'] == 'aff':
                    ref_id = xref.attrs['rid']
                    for aff in self.metadata.front.article_meta.aff:
                        if aff.attrs['id'] == ref_id:
                            if len(aff.addr_line) > 0:
                                addr = aff.addr_line[0].node
                                element_methods.append_new_text(editors_div, ', ')
                                element_methods.append_all_below(editors_div, addr)
                            else:
                                element_methods.append_new_text(editors_div, ', ')
                                element_methods.append_all_below(editors_div, aff.node)

    def make_article_info_dates(self, receiving_el):
        """
        Makes the section containing important dates for the article: typically
        Received, Accepted, and Published.
        """
        dates_div = etree.SubElement(receiving_el, 'div')
        dates_div.attrib['id'] = 'article-dates'

        if self.metadata.front.article_meta.history is not None:
            dates = self.metadata.front.article_meta.history.date
        else:
            dates = []
        received = None
        accepted = None
        for date in dates:
            if date.attrs['date-type'] is None:
                continue
            elif date.attrs['date-type'] == 'received':
                received = date
            elif date.attrs['date-type'] == 'accepted':
                accepted = date
            else:
                pass
        if received is not None:  # Optional
            b = etree.SubElement(dates_div, 'b')
            b.text = 'Received: '
            formatted_date_string = self.format_date_string(received)
            element_methods.append_new_text(dates_div, formatted_date_string+'; ')
        if accepted is not None:  # Optional
            b = etree.SubElement(dates_div, 'b')
            b.text = 'Accepted: '
            formatted_date_string = self.format_date_string(accepted)
            element_methods.append_new_text(dates_div, formatted_date_string+'; ')
        #Published date is required
        for pub_date in self.metadata.front.article_meta.pub_date:
            if pub_date.attrs['pub-type'] == 'epub':
                b = etree.SubElement(dates_div, 'b')
                b.text = 'Published: '
                formatted_date_string = self.format_date_string(pub_date)
                element_methods.append_new_text(dates_div, formatted_date_string)
                break

    def make_article_info_copyright(self, receiving_el):
        """
        Makes the copyright section for the ArticleInfo. For PLoS, this means
        handling the information contained in the metadata <permissions>
        element.
        """
        permissions = self.metadata.front.article_meta.permissions
        if permissions is None:  # Article contains no permissions element
            return
        copyright_div = etree.SubElement(receiving_el, 'div')
        copyright_div.attrib['id'] = 'copyright'
        cp_bold = etree.SubElement(copyright_div, 'b')
        cp_bold.text = 'Copyright: '
        copyright_string = '\u00A9 '
        if len(permissions.copyright_holder) > 0:
            copyright_string += element_methods.all_text(permissions.copyright_holder[0].node)
            copyright_string += '. ' 
        if len(permissions.license) > 0:  # I'm assuming only one license
            #Taking only the first license_p element
            license_p = permissions.license[0].license_p[0]
            #I expect to see only text in the 
            copyright_string += element_methods.all_text(license_p.node)
        element_methods.append_new_text(copyright_div, copyright_string)

    def make_article_info_funding(self, receiving_el):
        """
        Creates the element for declaring Funding in the article info.
        """
        funding_group = self.metadata.front.article_meta.funding_group
        if len(funding_group) == 0:
            return
        funding_div = etree.SubElement(receiving_el, 'div')
        funding_div.attrib['id'] = 'funding'
        funding_b = etree.SubElement(funding_div, 'b')
        funding_b.text = 'Funding: '
        #As far as I can tell, PLoS only uses one funding-statement
        funding_statement = funding_group[0].funding_statement[0]
        element_methods.append_all_below(funding_div, funding_statement.node)

    def make_article_info_competing_interests(self, receiving_el ):
        """
        Creates the element for declaring competing interests in the article
        info.
        """
        #Check for author-notes
        author_notes = self.metadata.front.article_meta.author_notes
        if author_notes is None:  # skip if not found
            return
        #Check each of the fn elements to see if they are a conflict of
        #interest statement
        conflict = None
        for fn in author_notes.fn:
            #This is a workaround, using lxml search, because of an odd issue
            #with the loading of the prescription of fn in the DTD
            fn_node = fn.node
            if 'fn-type' in fn_node.attrib:
                if fn_node.attrib['fn-type'] == 'conflict':
                    conflict = fn
                    break
        if conflict is None:  # Return since no conflict found
            return
        #Create the content
        conflict_div = etree.SubElement(receiving_el, 'div')
        conflict_div.attrib['id'] = 'conflict'
        conflict_b = etree.SubElement(conflict_div, 'b')
        conflict_b.text = 'Competing Interests: '
        #Grab the first paragraph in the fn element
        fn_p = conflict.node.find('p')
        if fn_p is not None:
            #Add all of its children to the conflict div
            element_methods.append_all_below(conflict_div, fn_p)

    def make_article_info_correspondences(self, receiving_el):
        """
        Articles generally provide a first contact, typically an email address
        for one of the authors. This will supply that content.
        """
        #Check for author-notes
        author_notes = self.metadata.front.article_meta.author_notes
        if author_notes is None:  # skip if not found
            return
        #Check for correspondences
        correspondence = author_notes.corresp
        if len(correspondence) == 0:  # Return since no correspondence found
            return
        corresp_div = etree.SubElement(receiving_el, 'div')
        corresp_div.attrib['id'] = 'correspondence'
        for corresp in correspondence:
            corresp_sub_div = etree.SubElement(corresp_div, 'div')
            corresp_sub_div.attrib['id'] = corresp.node.attrib['id']
            element_methods.append_all_below(corresp_sub_div, corresp.node)

    def make_article_info_footnotes_other(self, receiving_el):
        """
        This will catch all of the footnotes of type 'other' in the <fn-group>
        of the <back> element.
        """
        #Check for back, skip if it doesn't exist
        if self.metadata.back is None:
            return
        #Check for back fn-groups, skip if empty
        fn_groups = self.metadata.back.fn_group
        if len(fn_groups) == 0:
            return
        #Look for fn nodes of fn-type 'other'
        other_fns = []
        for fn_group in fn_groups:
            for fn in fn_group.fn:
                if not 'fn-type' in fn.node.attrib:
                    continue
                elif fn.node.attrib['fn-type'] == 'other':
                    other_fns.append(fn)
        if other_fns:
            other_fn_div = etree.SubElement(receiving_el, 'div', {'class': 'back-fn-other'})
        for other_fn in other_fns:
            element_methods.append_all_below(other_fn_div, other_fn.node)

    def make_back_matter(self, receiving_el):
        """
        The <back> element may have 0 or 1 <label> elements and 0 or 1 <title>
        elements. Then it may have any combination of the following: <ack>,
        <app-group>, <bio>, <fn-group>, <glossary>, <ref-list>, <notes>, and
        <sec>. <sec> is employed here as a catch-all for material that does not
        fall under the other categories.

        The Back should generally be thought of as a non-linear element, though
        some of its content will be parsed to the linear flow of the document.
        This can be thought of as critically important meta-information that
        should accompany the main text (e.g. Acknowledgments and Contributions)

        Because the content of <back> contains a set of tags that intersects
        with that of the Body, this method should always be called before the
        general post-processing steps; keep in mind that this is also the
        opportunity to permit special handling of content in the Back
        """
        #Back is technically metadata content that needs to be interpreted to
        #presentable content
        if self.metadata.back is None: 
            return
        #The following things are ordered in such a way to adhere to what
        #appears to be a consistent presentation order for PLoS
        #Acknowledgments
        self.make_back_acknowledgments(receiving_el)
        #Author Contributions
        self.make_back_author_contributions(receiving_el)
        #Glossaries
        self.make_back_glossary(receiving_el)
        #Notes
        self.make_back_notes(receiving_el)

    def make_back_acknowledgments(self, receiving_el):
        """
        The <ack> is an important piece of back matter information, and will be
        including immediately after the main text.

        This element should only occur once, optionally, for PLoS, if a need
        becomes known, then multiple instances may be supported.
        """
        if len(self.metadata.back.ack) == 0:
            return
        #Take a copy of the first ack element, using its xml form
        ack = deepcopy(self.metadata.back.ack[0].node)
        #Modify the tag to div
        ack.tag = 'div'
        #Give it an id
        ack.attrib['id'] = 'acknowledgments'
        #Give it a title element--this is not an OPS element but doing so will
        #allow it to later be depth-formatted by self.convert_div_titles()
        ack_title = etree.Element('title')
        ack_title.text = 'Acknowledgments'
        ack.insert(0, ack_title)
        #Append our modified copy of the first ack element to the receiving_el
        receiving_el.append(ack)

    def make_back_author_contributions(self, receiving_el):
        """
        Though this goes in the back of the document with the rest of the back
        matter, it is not an element found under <back>.

        I don't expect to see more than one of these. Compare this method to
        make_article_info_competing_interests()
        """
        #Check for author-notes
        author_notes = self.metadata.front.article_meta.author_notes
        if author_notes is None:  # skip if not found
            return
        #Check for contributions statement
        contribution = None
        #Grab the fn element for the contribution statement
        for fn in author_notes.fn:
            if 'fn-type' not in fn.node.attrib:
                continue
            elif fn.node.attrib['fn-type'] == 'con':
                contribution = fn
                break
        if not contribution:
            return
        #Create a deepcopy of the fn to modify and add to the receiving_el
        author_contrib = deepcopy(contribution.node)
        element_methods.remove_all_attributes(author_contrib)
        author_contrib.tag = 'div'
        author_contrib.attrib['id'] = 'author-contributions'
        #Give it a title element--this is not an OPS element but doing so will
        #allow it to later be depth-formatted by self.convert_div_titles()
        contributions_title = etree.Element('title')
        contributions_title.text = 'Author Contributions'
        author_contrib.insert(0, contributions_title)
        #Append the modified copy of the author contribution fn to receiving_el
        receiving_el.append(author_contrib)

    def make_back_glossary(self, receiving_el):
        """
        Glossaries are a fairly common item in papers for PLoS, but it also
        seems that they are rarely incorporated into the PLoS web-site or PDF
        formats. They are included in the ePub output however because they are
        helpful and because we can.
        """
        #Check if self.back exists
        glossaries = self.metadata.back.glossary
        if len(glossaries) == 0:
            return
        for glossary in glossaries:
            glossary_copy = deepcopy(glossary.node)
            glossary_copy.tag = 'div'
            glossary_copy.attrib['class'] = 'back-glossary'
            receiving_el.append(glossary_copy)

    def make_back_notes(self, receiving_el):
        """
        The notes element in PLoS articles can be employed for posting notices
        of corrections or adjustments in proof. The <notes> element has a very
        diverse content model, but PLoS practice appears to be fairly
        consistent: a single <sec> containing a <title> and a <p>
        """
        all_notes = self.metadata.back.notes
        if len(all_notes) == 0:
            return
        for notes in all_notes:
            notes_sec = deepcopy(notes.sec[0].node)
            notes_sec.tag = 'div'
            notes_sec.attrib['class'] = 'back-notes'
            receiving_el.append(notes_sec)

    def format_date_string(self, date_tuple):
        """
        Receives a date_tuple object, defined in jptsmeta, and outputs a string
        for placement in the article content.
        """
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        date_string = ''
        if date_tuple.season:
            return '{0}, {1}'.format(date_tuple.season.text, date_tuple.year.text)
        else:
            if not date_tuple.month and not date_tuple.day:
                return '{0}'.format(date_tuple.year.text)
            if date_tuple.month:
                date_string += months[int(date_tuple.month.text)]
            if date_tuple.day:
                date_string += ' ' + date_tuple.day.text
            return ', '.join([date_string, date_tuple.year.text])

    def format_self_citation(self):
        """
        PLoS articles present a citation for the article itself. This method
        will return the citation for the article as a string.
        """
        #This is not yet fully implemented.
        #I need clarification/documentation from PLoS
        #So for now I just put in the DOI
        return self.doi

    def convert_fig_elements(self, top):
        """
        Responsible for the correct conversion of JPTS 3.0 <fig> elements to
        OPS xhtml. Aside from translating <fig> to <img>, the content model
        must be edited.
        """
        figs = top.findall('.//fig')
        for fig in figs:
            if fig.getparent().tag == 'p':
                element_methods.elevate_element(fig)
        for fig in figs:
            #self.convert_fn_elements(fig)
            #self.convert_disp_formula_elements(fig)
            #Find label and caption
            label_el = fig.find('label')
            caption_el = fig.find('caption')
            #Get the graphic node, this should be mandatory later on
            graphic_el = fig.find('graphic')
            #Create a file reference for the image
            xlink_href = element_methods.ns_format(graphic_el, 'xlink:href')
            graphic_xlink_href = graphic_el.attrib[xlink_href]
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_frag
            img_path = '/'.join([img_dir, file_name])

            #Create the OPS content: using image path, label, and caption
            img_el = etree.Element('img', {'alt': 'A Figure', 'src': img_path,
                                           'class': 'figure'})
            if 'id' in fig.attrib:
                img_el.attrib['id'] = fig.attrib['id']
            element_methods.insert_before(fig, img_el)

            #Create content for the label and caption
            if caption_el is not None or label_el is not None:
                img_caption_div = etree.Element('div', {'class': 'figure-caption'})
                img_caption_div_b = etree.SubElement(img_caption_div, 'b')
                if label_el is not None:
                    element_methods.append_all_below(img_caption_div_b, label_el)
                    element_methods.append_new_text(img_caption_div_b, '. ', join_str='')
                if caption_el is not None:
                    caption_title = caption_el.find('title')
                    if caption_title is not None:
                        element_methods.append_all_below(img_caption_div_b, caption_title)
                        element_methods.append_new_text(img_caption_div_b, ' ', join_str='')
                    for each_p in caption_el.findall('p'):
                        element_methods.append_all_below(img_caption_div, each_p)
                element_methods.insert_before(fig, img_caption_div)

            #Remove the original <fig>
            element_methods.remove(fig)

    def convert_table_wrap_elements(self, top):
        """
        Responsible for the correct conversion of JPTS 3.0 <table-wrap>
        elements to OPS content.
        
        The 'id' attribute is treated as mandatory by this method.
        """
        for table_wrap in top.findall('.//table-wrap'):
            #TODO: Address table uncommenting, for now this is not workable
            #for child in tab.childNodes:
            #    if child.nodeType == 8:
            #        element_methods.uncomment(child)
            
            #Create a div for all of the table stuff
            table_div = etree.Element('div')
            table_div.attrib['id'] = table_wrap.attrib['id']

            #Get the optional label and caption
            label = table_wrap.find('label')
            caption = table_wrap.find('caption')
            #Check for the alternatives element
            alternatives = table_wrap.find('alternatives')
            #Look for the graphic node, under table-wrap and alternatives
            graphic = table_wrap.find('graphic')
            if graphic is None and alternatives is not None:
                graphic = alternatives.find('graphic')
            #Look for the table node, under table-wrap and alternatives
            table = table_wrap.find('table')
            if table is None and alternatives is not None:
                table = alternatives.find('table')

            #Handling the label and caption
            if label is not None and caption is not None:
                caption_div = etree.Element('div', {'class': 'table-caption'})
                caption_div_b = etree.SubElement(caption_div, 'b')
                if label is not None:
                    element_methods.append_all_below(caption_div_b, label)
                if caption is not None:
                    #Find, optional, title element and paragraph elements
                    caption_title = caption.find('title')
                    if caption_title is not None:
                        element_methods.append_all_below(caption_div_b, caption_title)
                    caption_ps = caption.findall('p')
                    #For title and each paragraph, give children to the div
                    for caption_p in caption_ps:
                        element_methods.append_all_below(caption_div, caption_p)
                #Add this to the table div
                table_div.append(caption_div)

            ### Practical Description ###
            #A table may have both, one of, or neither of graphic and table
            #The different combinations should be handled, but a table-wrap
            #with neither should fail with an error
            #
            #If there is both an image and a table, the image should be placed
            #in the text flow with a link to the html table
            #
            #If there is an image and no table, the image should be placed in
            #the text flow without a link to an html table
            #
            #If there is a table with no image, then the table should be placed
            #in the text flow.
            
            if graphic is not None:
                #Create the image path for the graphic
                xlink_href = element_methods.ns_format(graphic, 'xlink:href')
                graphic_xlink_href = graphic.attrib[xlink_href]
                file_name = graphic_xlink_href.split('.')[-1] + '.png'
                img_dir = 'images-' + self.doi_frag
                img_path = '/'.join([img_dir, file_name])
                #Create the new img element
                img_element = etree.Element('img', {'alt': 'A Table',
                                                    'src': img_path,
                                                    'class': 'table'})
                #Add this to the table div
                table_div.append(img_element)
                #If table, add it to the list, and link to it
                if table is not None:  # Both graphic and table
                    #The label attribute is just a means of transmitting some
                    #plaintext which will be used for the labeling in the html
                    #tables file
                    if label is not None:
                        #Serialize the text, set as label attribute
                        table.attrib['label'] = str(etree.tostring(label, method='text', encoding='utf-8'), encoding='utf-8')
                    table.attrib['id'] = table_wrap.attrib['id']
                    #Add the table to the tables list
                    self.html_tables.append(table)
                    #Also add the table's foot if it exists
                    table_wrap_foot = table_wrap.find('table-wrap-foot')
                    if table_wrap_foot is not None:
                        self.html_tables.append(table_wrap_foot)
                    #Create a link to the html version of the table
                    html_table_link = etree.Element('a')
                    html_table_link.attrib['href'] = self.tab_frag.format(table_wrap.attrib['id'])
                    html_table_link.text = 'Go to HTML version of this table'
                    #Add this to the table div
                    table_div.append(html_table_link)

            elif table is not None:  # Table only
                #Simply append the table to the table div
                table_div.append(table)
            elif graphic is None and table is None:
                print('Encountered table-wrap element with neither graphic nor table. Exiting.')
                sys.exit(1)

            #Replace the original table-wrap with the newly constructed div
            element_methods.replace(table_wrap, table_div)
        #Finally done

    def convert_sec_elements(self, body):
        """
        Convert <sec> elements to <div> elements and handle ids and attributes
        """
        #Find all <sec> in body
        sec_elements = body.findall('.//sec')
        count = 0
        #Convert the sec elements
        for sec in sec_elements:
            sec.tag = 'div'
            element_methods.rename_attributes(sec, {'sec-type': 'class'})
            if 'id' not in sec.attrib:  # Give it an id if it is missing
                sec.attrib['id'] = 'OA-EPUB-{0}'.format(str(count))
                count += 1

    def convert_div_titles(self, element, depth=0):
        """
        A recursive function to convert <title> nodes directly beneath <div>
        nodes into appropriate OPS compatible header tags.

        A div element may or may not have a label sub-element, and it may or
        may not have a title sub-element. This results in 4 unique scenarios.
        Having an empty title element, or an empty label element, will be
        treated as not having the element at all.
        """
        depth_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
        #Look for divs
        for div in element.findall('div'):
            #Look for a label
            div_label = div.find('label')
            if div_label is not None:
                #Check if empty, no elements and no text
                if len(div_label) == 0 and div_label.text is None:
                    div_label.getparent().remove(div_label)  # remove the element from the tree
                    div_label = None
            #Look for a title
            div_title = div.find('title')
            if div_title is not None:
                #Check if empty, no elements and no text
                if len(div_title) == 0 and div_title.text is None:
                    div_title.getparent().remove(div_title)  # remove the element from the tree
                    div_title = None
            #Now we have div_label and div_title (they may be None)
            #If there is a div_title
            if div_title is not None:
                #Rename the tag
                if depth < len(depth_tags):
                    div_title.tag = depth_tags[depth]
                else:
                    div_title.tag = 'span'
                    div_title.attrib['class'] = 'extendedheader{0}'.format(depth+2)
                #If there is a div_label
                if div_label is not None:
                    #Prepend the label text to the title
                    div_title.text = ' '.join(div_label.text, div_title.text)
                    div_label.getparent().remove(div_label)  # Remove the label
            elif div_label is not None:  # No title, but there is a label
                #Rename the tag
                div_label.tag = 'b'  # Convert to a bold element
            else:  # Neither label nor title
                pass

            #Move on to the next level
            self.convert_div_titles(div, depth=depth+1)

    def convert_xref_elements(self, top):
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
                   'aff': self.main_frag,
                   'sec': self.main_frag,
                   'table-fn': self.tab_frag,
                   'boxed-text': self.main_frag,
                   'other': self.main_frag,
                   'disp-formula': self.main_frag,
                   'fn': self.main_frag,
                   'app': self.main_frag,
                   '': self.main_frag}
        for xref in top.findall('.//xref'):
            xref.tag = 'a'
            xref_attrs = copy(xref.attrib)
            element_methods.remove_all_attributes(xref)
            if 'ref-type' in xref_attrs:
                ref_type = xref_attrs['ref-type']
            else:
                ref_type = ''
            rid = xref_attrs['rid']
            address = ref_map[ref_type].format(rid)
            xref.attrib['href'] = address

    def convert_disp_formula_elements(self, top):
        """
        <disp-formula> elements must be converted to OPS conforming elements
        """
        disp_formulas = top.findall('.//disp-formula')
        for disp in disp_formulas:
            #find label element
            label_el = disp.find('label')
            graphic_el = disp.find('graphic')
            if graphic_el is None:  # No graphic, assume math as text instead
                text_span = etree.Element('span', {'class': 'disp-formula'})
                if 'id' in disp.attrib:
                    text_span.attrib['id'] = disp.attrib['id']
                element_methods.append_all_below(text_span, disp)
                #Insert the text span before the disp-formula
                element_methods.insert_before(disp, text_span)
                #If a label exists, modify and insert before text_span
                if label_el is not None:
                    label_el.tag = 'b'
                    element_methods.insert_before(text_span, label_el)
                #Remove the disp-formula
                element_methods.remove(disp)
                #Skip the rest, which deals with the graphic element
                continue
            #The graphic element is present
            #Create a file reference for the image
            xlink_href = element_methods.ns_format(graphic_el, 'xlink:href')
            graphic_xlink_href = graphic_el.attrib[xlink_href]
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_frag
            img_path = '/'.join([img_dir, file_name])

            #Create OPS content, using image path, and label
            #Create the img element
            img_element = etree.Element('img', {'alt': 'A Display Formula',
                                                'class': 'disp-formula',
                                                'src': img_path})
            #Transfer the id attribute
            if 'id' in disp.attrib:
                img_element.attrib['id'] = disp.attrib['id']
            #Insert the img element
            element_methods.insert_before(disp, img_element)
            #Create content for the label
            if label_el is not None:
                label_el.tag = 'b'
                element_methods.insert_before(img_element, label_el)
            #Remove the old disp-formula element
            element_methods.remove(disp)

    def convert_inline_formula_elements(self, top):
        """
        <inline-formula> elements must be converted to OPS conforming elements

        These elements may contain <inline-graphic> elements, textual content,
        or both.
        """
        inline_formulas = top.findall('.//inline-formula')
        for inline in inline_formulas:
            #inline-formula elements will be modified in situ
            element_methods.remove_all_attributes(inline)
            inline.tag = 'span'
            inline.attrib['class'] = 'inline-formula'
            inline_graphic = inline.find('inline-graphic')
            if inline_graphic is None:
                # Do nothing more if there is no graphic
                continue
            #Need to conver the inline-graphic element to an img element
            inline_graphic.tag = 'img'
            #Get a copy of the attributes, then remove them
            inline_graphic_attributes = copy(inline_graphic.attrib)
            element_methods.remove_all_attributes(inline_graphic)
            #Create a file reference for the image
            xlink_href = element_methods.ns_format(inline_graphic, 'xlink:href')
            graphic_xlink_href = inline_graphic_attributes[xlink_href]
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_frag
            img_path = '/'.join([img_dir, file_name])
            #Set the source to the image path
            inline_graphic.attrib['src'] = img_path
            inline_graphic.attrib['class'] = 'inline-formula'
            inline_graphic.attrib['alt'] = 'An Inline Formula'

    def convert_named_content_elements(self, top):
        """
        <named-content> elements are used by PLoS for certain spcecial kinds
        of content, such as genus-species denotations. This method will convert
        the tagname to <span> and the content-type attribute to class. I expect
        that this will provide an easily extensible basis for CSS handling.
        """
        for named_content in top.findall('.//named-content'):
            named_content.tag = 'span'
            attrs = copy(named_content.attrib)
            element_methods.remove_all_attributes(named_content)
            if 'content-type' in attrs:
                named_content.attrib['class'] = attrs['content-type']

    def convert_disp_quote_elements(self, top):
        """
        Extract or extended quoted passage from another work, usually made
        typographically distinct from surrounding text

        <disp-quote> elements have a relatively complex content model, but PLoS
        appears to employ either <p>s or <list>s.
        """
        for disp_quote in top.findall('.//disp-quote'):
            if disp_quote.getparent().tag =='p':
                element_methods.elevate_element(disp_quote)
            disp_quote.tag = 'div'
            disp_quote.attrib['class'] = 'disp-quote'

    def convert_boxed_text_elements(self, top):
        """
        Textual material that is part of the body of text but outside the
        flow of the narrative text, for example, a sidebar, marginalia, text
        insert (whether enclosed in a box or not), caution, tip, note box, etc.

        <boxed-text> elements for PLoS appear to all contain a single <sec>
        element which frequently contains a <title> and various other content.
        This method will elevate the <sec> element, adding class information as
        well as processing the title.
        """
        for boxed_text in top.findall('.//boxed-text'):
            sec_el = boxed_text.find('sec')
            if sec_el is not None:
                sec_el.tag = 'div'
                title = sec_el.find('title')
                if title is not None:
                    title.tag = 'b'
                sec_el.attrib['class'] = 'boxed-text'
                if 'id' in boxed_text.attrib:
                    sec_el.attrib['id'] = boxed_text.attrib['id']
                element_methods.replace(boxed_text, sec_el)
                continue
            else:
                div_el = etree.Element('div', {'class': 'boxed-text'})
                if 'id' in boxed_text.attrib:
                    div_el.attrib['id'] = boxed_text.attrib['id']
                element_methods.append_all_below(div_el, boxed_text)
                element_methods.replace(boxed_text, div_el)

    def convert_supplementary_material_elements(self, top):
        """
        Supplementary material are not, nor are they generally expected to be,
        packaged into the epub file. Though this is a technical possibility,
        and certain epub reading systems (such as those run on a PC) might be
        reasonably capable of the external handling of diverse file formats
        I presume that supplementary material will remain separate from the
        document. So special cases aside, external links to supplementary
        material will be employed; this will require internet connection for
        access.

        As for content in <supplementary-material>, they appear to strictly
        contain 1 <label> element, followed by a <caption><title><p></caption>
        substructure.
        """
        supplementary_materials = top.findall('.//supplementary-material')
        for supplementary in supplementary_materials:
            #Create a div element to hold the supplementary content
            suppl_div = etree.Element('div')
            if 'id' in supplementary.attrib:
                suppl_div.attrib['id'] = supplementary.attrib['id']
            element_methods.insert_before(supplementary, suppl_div)
            #Get the sub elements
            label = supplementary.find('label')
            caption = supplementary.find('caption')
            #Get the external resource URL for the supplementary information
            ns_xlink_href = element_methods.ns_format(supplementary, 'xlink:href')
            xlink_href = supplementary.attrib[ns_xlink_href]
            resource_url = self.fetch_single_representation(xlink_href)
            if label is not None:
                label.tag = 'a'
                label.attrib['href'] = resource_url
                element_methods.append_new_text(label, '. ', join_str='')
                suppl_div.append(label)
            if caption is not None:
                title = caption.find('title')
                paragraphs = caption.findall('p')
                if title is not None:
                    title.tag = 'b'
                    suppl_div.append(title)
                for paragraph in paragraphs:
                    suppl_div.append(paragraph)
            element_methods.remove(supplementary)

    def convert_verse_group_elements(self, top):
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
        for verse_group in top.findall('.//verse-group'):
            #Find some possible sub elements for the heading
            label = verse_group.find('label')
            title = verse_group.find('title')
            subtitle = verse_group.find('subtitle')
            #Modify the verse-group element
            verse_group.tag = 'div'
            verse_group.attrib['id'] = 'verse-group'
            #Create a title for the verse_group
            if label is not None or title is not None or subtitle is not None:
                new_verse_title = etree.Element('b')
                #Insert it at the beginning
                verse_group.insert(0, new_verse_title)
                #Induct the title elements into the new title
                if label is not None:
                    element_methods.append_all_below(new_verse_title, label)
                    element_methods.remove(label)
                if title is not None:
                    element_methods.append_all_below(new_verse_title, title)
                    element_methods.remove(title)
                if subtitle is not None:
                    element_methods.append_all_below(new_verse_title, subtitle)
                    element_methods.remove(subtitle)
            for verse_line in verse_group.findall('verse-line'):
                verse_line.tag = 'p'
                verse_line.attrib['class'] = 'verse-line'

    def convert_fn_elements(self, top):
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
        footnotes = top.findall('.//fn')
        for footnote in footnotes:
            #Use only the first paragraph
            paragraph = footnote.find('p')
            #If no paragraph, move on
            if paragraph is None:
                element_methods.remove(footnote)
                continue
            #Simply remove corrected errata items
            paragraph_text = str(etree.tostring(paragraph, method='text', encoding='utf-8'), encoding='utf-8')
            if paragraph_text.startswith('Erratum') and 'Corrected' in paragraph_text:
                element_methods.remove(footnote)
                continue
            #Transfer some attribute information from the fn element to the paragraph
            if 'id' in footnote.attrib:
                paragraph.attrib['id'] = footnote.attrib['id']
            if 'fn-type' in footnote.attrib:
                paragraph.attrib['class'] = 'fn-type-{0}'.footnote.attrib['fn-type']
            else:
                paragraph.attrib['class'] = 'fn'
                #Replace the 
            element_methods.replace(footnote, paragraph)

    def convert_list_elements(self, top):
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

        #This is a block level element, so elevate it if found in p
        for list_el in top.findall('.//list'):
            if list_el.getparent().tag == 'p':
                element_methods.elevate_element(list_el)

        #list_el is used instead of list (list is reserved)
        for list_el in top.findall('.//list'):
            if 'list-type' not in list_el.attrib:
                list_el_type = 'order'
            else:
                list_el_type = list_el.attrib['list-type']
            #Unordered lists
            if list_el_type in ['', 'bullet', 'simple']:
                list_el.tag = 'ul'
                #CSS must be used to recognize the class and suppress bullets
                if list_el_type == 'simple':
                    list_el.attrib['class'] = 'simple'
            #Ordered lists
            else:
                list_el.tag = 'ol'
                list_el.attrib['class'] = list_el_type
            #Convert the list-item element tags to 'li'
            for list_item in list_el.findall('list-item'):
                list_item.tag = 'li'
            element_methods.remove_all_attributes(list_el, exclude=['id', 'class'])

    def convert_def_list_elements(self, top):
        """
        A list in which each item consists of two parts: a word, phrase, term,
        graphic, chemical structure, or equation paired with one of more
        descriptions, discussions, explanations, or definitions of it.

        <def-list> elements are lists of <def-item> elements which are in turn
        composed of a pair of term (<term>) and definition (<def>). This method
        will convert the <def-list> to a classed <div> with a styled format
        for the terms and definitions.
        """
        for def_list in top.findall('.//def-list'):
            #Remove the attributes, excepting id
            element_methods.remove_all_attributes(def_list, exclude=['id'])
            #Modify the def-list element
            def_list.tag = 'div'
            def_list.attrib['class'] = 'def-list'
            for def_item in def_list.findall('def-item'):
                #Get the term being defined, modify it
                term = def_item.find('term')
                term.tag = 'p'
                term.attrib['class']= 'def-item-term'
                #Insert it before its parent def_item
                element_methods.insert_before(def_item, term)
                #Get the definition, handle missing with a warning
                definition = def_item.find('def')
                if definition is None:
                    log.warning('Missing def element in def-item')
                    element_methods.remove(def_item)
                #PLoS appears to consistently place all definition text in a
                #paragraph subelement of the def element
                def_para = definition.find('p')
                def_para.attrib['class'] = 'def-item-def'
                #Replace the def-item element with the p element
                element_methods.replace(def_item, def_para)

    def convert_ref_list_elements(self, top):
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
        #TODO: Handle nested ref-lists
        for ref_list in top.findall('.//ref-list'):
            element_methods.remove_all_attributes(ref_list)
            ref_list.tag = 'div'
            ref_list.attrib['class'] = 'ref-list'
            label = ref_list.find('label')
            if label is not None:
                label.tag = 'h3'
            for ref in ref_list.findall('ref'):
                ref_p = etree.Element('p')
                ref_p.text = str(etree.tostring(ref, method='text', encoding='utf-8'), encoding='utf-8')
                element_methods.replace(ref, ref_p)

    def convert_graphic_elements(self, top):
        """
        This is a method for the odd special cases where <graphic> elements are
        standalone, or rather, not a part of a standard graphical element such
        as a figure or a table. This method should always be employed after the
        standard cases have already been handled.
        """
        for graphic in top.findall('.//graphic'):
            graphic.tag = 'img'
            ns_xlink_href = element_methods.ns_format(graphic, 'xlink:href')
            graphic.attrib['alt'] = 'unowned-graphic'
            if ns_xlink_href in graphic.attrib:
                xlink_href = graphic_attributes[ns_xlink_href]
                file_name = xlink_href.split('.')[-1] + '.png'
                img_dir = 'images-' + self.doi_frag
                img_path = '/'.join([img_dir, file_name])
                graphic.attrib['src'] = img_path
            element_methods.remove_all_attributes(graphic, exclude=['id', 'class', 'alt', 'src'])

    def fetch_single_representation(self, item_xlink_href):
        """
        This function will render a formatted URL for accessing the PLoS' server
        SingleRepresentation of an object.
        """
        #A dict of URLs for PLoS subjournals
        journal_urls = {'pgen': 'http://www.plosgenetics.org/article/{0}',
                        'pcbi': 'http://www.ploscompbiol.org/article/{0}',
                        'ppat': 'http://www.plospathogens.org/article/{0}',
                        'pntd': 'http://www.plosntds.org/article/{0}',
                        'pmed': 'http://www.plosmedicine.org/article/{0}',
                        'pbio': 'http://www.plosbiology.org/article/{0}',
                        'pone': 'http://www.plosone.org/article/{0}',
                        'pctr': 'http://clinicaltrials.ploshubs.org/article/{0}'}
        #Identify subjournal name for base URl
        subjournal_name = self.doi_frag.split('.')[1]
        base_url = journal_urls[subjournal_name]
    
        #Compose the address for fetchSingleRepresentation
        resource = 'fetchSingleRepresentation.action?uri=' + item_xlink_href
        return base_url.format(resource)
