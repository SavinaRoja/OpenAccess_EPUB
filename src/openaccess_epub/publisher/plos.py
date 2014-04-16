# -*- coding: utf-8 -*-

"""
"""

#Standard Library modules
import logging
from copy import deepcopy

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub.publisher import (
    Publisher,
    contributor_tuple,
    date_tuple,
    identifier_tuple
)
from openaccess_epub.utils.element_methods import *


class PLoS(Publisher):
    def __init__(self, article):
        super(PLoS, self).__init__(article)
        self.epub2_support = True
        self.epub3_support = True

    def nav_contributors(self):
        contributor_list = []
        for contrib_group in self.article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if not contrib.attrs['contrib-type'] == 'author':
                    continue
                if contrib.collab:
                    auth = serialize(contrib.collab[0].node, strip=True)
                    file_as = auth
                elif contrib.anonymous:
                    auth = 'Anonymous'
                    file_as = auth
                else:
                    name = contrib.name[0]  # Work with only first name listed
                    surname = name.surname.text
                    given = name.given_names
                    if given:  # Given is optional
                        if given.text:  # Odd instances of empty tags
                            auth = ' '.join([surname, given.text])
                            given_initial = given.text[0]
                            file_as = ', '.join([surname, given_initial])
                        else:
                            auth = surname
                            file_as = auth
                    else:
                        auth = surname
                        file_as = auth
                new_contributor = contributor_tuple(auth, 'aut', file_as)
                contributor_list.append(new_contributor)
        return contributor_list

    def nav_title(self):
        #Serializes the article-title element, since it is not just text
        article_title = self.article.metadata.front.article_meta.title_group.article_title.node
        return serialize(article_title, strip=True)

    def package_identifier(self):
        #Returning the DOI
        return identifier_tuple(self.article.doi, 'DOI')

    def package_language(self):
        #All PLoS articles are published in English
        return ['en']

    def package_title(self):
        #Sends the same result as for the Navigation Document
        return self.nav_title()

    def package_contributor(self):
        contributor_list = []
        for contrib_group in self.article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                contrib_type = contrib.attrs['contrib-type']
                if contrib.collab:
                    auth = serialize(contrib.collab[0].node)
                    file_as = auth
                elif contrib.anonymous:
                    auth = 'Anonymous'
                    file_as = auth
                else:
                    name = contrib.name[0]  # Work with only first name listed
                    surname = name.surname.text
                    given = name.given_names
                    if given:  # Given is optional
                        if given.text:  # Odd instances of empty tags
                            auth = ' '.join([surname, given.text])
                            given_initial = given.text[0]
                            file_as = ', '.join([surname, given_initial])
                        else:
                            auth = surname
                            file_as = auth
                    else:
                        auth = surname
                        file_as = auth
                if contrib_type == 'editor':
                    role = 'edt'
                elif contrib_type == 'author':
                    role = 'aut'
                else:
                    continue
                new_contributor = contributor_tuple(auth, role, file_as)
                contributor_list.append(new_contributor)
        return contributor_list

    def package_publisher(self):
        return 'Public Library of Science'

    def package_description(self):
        """
        Given an Article class instance, this is responsible for returning an
        article description. For this method I have taken the approach of
        serializing the article's first abstract, if it has one. This results
        in 0 or 1 descriptions per article.
        """
        abstract = self.article.metadata.front.article_meta.abstract
        abst_text = serialize(abstract[0].node, strip=True) if abstract else ''
        return abst_text

    def package_date(self):
        #This method looks specifically to locate the dates of PLoS acceptance
        #and publishing online
        date_list = []
        #Creation is a Dublin Core event value: I interpret it as the date of acceptance
        history = self.article.metadata.front.article_meta.history
        #For some reason, the lxml dtd parser fails to recognize the content model of
        #history (something to do with expanded content model? I am not sure yet)
        #So for now, this will illustrate a work-around using lxml search
        if history is not None:
            for date in history.node.findall('date'):
                if not 'date-type' in date.attrib:
                    continue
                if date.attrib['date-type'] in ['accepted', 'received']:
                    year_el = date.find('year')
                    month_el = date.find('month')
                    day_el = date.find('day')
                    year = all_text(year_el) if year_el is not None else ''
                    month = all_text(month_el) if month_el is not None else ''
                    day = all_text(day_el) if day_el is not None else ''
                    if date.attrib['date-type'] == 'accepted':
                        date_list.append(date_tuple(year,
                                                    month,
                                                    day,
                                                    'accepted'))
                    elif date.attrib['date-type'] == 'received':
                        date_list.append(date_tuple(year,
                                                    month,
                                                    day,
                                                    'submitted'))

        #Publication is another Dublin Core event value: I use date of epub
        pub_dates = self.article.metadata.front.article_meta.pub_date
        for pub_date in pub_dates:
            if pub_date.attrs['pub-type'] == 'epub':
                date_list.append(date_tuple(pub_date.year.text,
                                            pub_date.month.text,
                                            pub_date.day.text,
                                            'copyrighted'))
        return date_list

    def package_subject(self):
        #Concerned only with kwd elements, not compound-kwd elements
        #Basically just compiling a list of their serialized text
        subject_list = []
        kwd_groups = self.article.metadata.front.article_meta.kwd_group
        for kwd_group in kwd_groups:
            for kwd in kwd_group.kwd:
                subject_list.append(serialize(kwd.node))
        return subject_list

    def package_rights(self):
        #Perhaps we could just return a static string if everything in PLoS is
        #published under the same license. But this inspects the file
        rights = self.article.metadata.front.article_meta.permissions.license
        return serialize(rights[0].node)

    @Publisher.maker2
    @Publisher.maker3
    def make_heading(self):
        body = self.main.getroot().find('body')
        heading_div = etree.Element('div')
        body.insert(0, heading_div)
        heading_div.attrib['id'] = 'Heading'
        #Creation of the title
        heading_div.append(self.heading_title())
        #Creation of the Authors
        list_of_authors = self.get_authors_list()
        heading_div.append(self.make_heading_authors(list_of_authors))
        #Creation of the Authors Affiliations text
        self.make_heading_affiliations(heading_div)
        #Creation of the Abstract content for the Heading
        self.make_heading_abstracts(heading_div)

    def heading_title(self):
        """
        Makes the Article Title for the Heading.

        Metadata element, content derived from FrontMatter
        """
        article_title = deepcopy(self.article.metadata.front.article_meta.title_group.article_title.node)
        article_title.tag = 'h1'
        article_title.attrib['id'] = 'title'
        article_title.attrib['class'] = 'article-title'
        return article_title

    def make_heading_authors(self, authors):
        """
        Constructs the Authors content for the Heading. This should display
        directly after the Article Title.

        Metadata element, content derived from FrontMatter
        """
        author_element = etree.Element('h3', {'class': 'authors'})
        #Construct content for the author element
        first = True
        for author in authors:
            if first:
                first = False
            else:
                append_new_text(author_element, ',', join_str='')
            if len(author.collab) > 0:  # If collab, just add rich content
                #Assume only one collab
                append_all_below(author_element, author.collab[0].node)
            elif len(author.anonymous) > 0:  # If anonymous, just add "Anonymous"
                append_new_text(author_element, 'Anonymous')
            else:  # Author is neither Anonymous or a Collaboration
                name = author.name[0]  # Work with only first name listed
                surname = name.surname.text
                if name.given_names is not None:
                    name_text = ' '.join([name.given_names.text, surname])
                else:
                    name_text = surname
                append_new_text(author_element, name_text)
            #TODO: Handle author footnote references, also put footnotes in the ArticleInfo
            #Example: journal.pbio.0040370.xml
            first = True
            for xref in author.xref:
                if xref.attrs['ref-type'] in ['corresp', 'aff']:
                    try:
                        sup_element = xref.sup[0].node
                    except IndexError:
                        sup_text = ''
                    else:
                        sup_text = all_text(sup_element)
                    new_sup = etree.SubElement(author_element, 'sup')
                    sup_link = etree.SubElement(new_sup, 'a')
                    sup_link.attrib['href'] = self.main_fragment.format(xref.attrs['rid'])
                    sup_link.text = sup_text
                    if first:
                        first = False
                    else:
                        new_sup.text = ','
        return author_element

    def make_heading_affiliations(self, heading_div):
        """
        Makes the content for the Author Affiliations, displays after the
        Authors segment in the Heading.

        Metadata element, content derived from FrontMatter
        """
        #Get all of the aff element tuples from the metadata
        affs = self.article.metadata.front.article_meta.aff
        #Create a list of all those pertaining to the authors
        author_affs = [i for i in affs if 'aff' in i.attrs['id']]
        #Count them, used for formatting
        if len(author_affs) == 0:
            return None
        else:
            affs_list = etree.SubElement(heading_div,
                                         'ul',
                                         {'id': 'affiliations',
                                          'class': 'simple'})

        #A simple way that seems to work by PLoS convention, but does not treat
        #the full scope of the <aff> element
        for aff in author_affs:
            #Expecting id to always be present
            aff_id = aff.attrs['id']
            #Create a span element to accept extracted content
            aff_item = etree.SubElement(affs_list, 'li')
            aff_item.attrib['id'] = aff_id
            #Get the first label node and the first addr-line node
            if len(aff.label) > 0:
                label = aff.label[0].node
                label_text = all_text(label)
                bold = etree.SubElement(aff_item, 'b')
                bold.text = label_text + ' '
            if len(aff.addr_line) > 0:
                addr_line = aff.addr_line[0].node
                append_new_text(aff_item, all_text(addr_line))
            else:
                append_new_text(aff_item, all_text(aff))

    def make_heading_abstracts(self, heading_div):
        """
        An article may contain data for various kinds of abstracts. This method
        works on those that are included in the Heading. This is displayed
        after the Authors and Affiliations.

        Metadata element, content derived from FrontMatter
        """
        for abstract in self.article.metadata.front.article_meta.abstract:
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
            remove_all_attributes(abstract_copy)
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
            heading_div.append(abstract_header)
            heading_div.append(abstract_copy)

    def get_authors_list(self):
        """
        Gets a list of all authors described in the metadata.
        """
        authors_list = []
        for contrib_group in self.article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if contrib.attrs['contrib-type'] == 'author':
                    authors_list.append(contrib)
        return authors_list

    def get_editors_list(self):
        """
        Gets a list of all editors described in the metadata.
        """
        editors_list = []
        for contrib_group in self.article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if contrib.attrs['contrib-type'] == 'editor':
                    editors_list.append(contrib)
        return editors_list

    @Publisher.maker2
    @Publisher.maker3
    def make_article_info(self):
        """
        The Article Info contains the (self) Citation, Editors, Dates,
        Copyright, Funding Statement, Competing Interests Statement,
        Correspondence, and Footnotes. Maybe more...

        This content follows the Heading and precedes the Main segment in the
        output.

        This function accepts the receiving_node argument, which will receive
        all generated output as new childNodes.
        """
        body = self.main.getroot().find('body')
        #Create a div for ArticleInfo, exposing it to linking and formatting
        article_info_div = etree.Element('div', {'id': 'ArticleInfo'})
        body.insert(1, article_info_div)
        #Creation of the self Citation
        article_info_div.append(self.make_article_info_citation())
        #Creation of the Editors
        list_of_editors = self.get_editors_list()
        self.make_article_info_editors(list_of_editors, article_info_div)
        #Creation of the important Dates segment
        article_info_div.append(self.make_article_info_dates())
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

    def make_article_info_citation(self):
        """
        Creates a self citation node for the ArticleInfo of the article.

        This method uses code from this page as a reference implementation:
        https://github.com/PLOS/ambra/blob/master/base/src/main/resources/articleTransform-v3.xsl
        """
        citation_div = etree.Element('div', {'id': 'article-citation'})
        b = etree.SubElement(citation_div, 'b')
        b.text = 'Citation: '

        #Add author stuff to the citation
        author_list = self.get_authors_list()
        for author in author_list:
            author_index = author_list.index(author)
            #At the 6th author, simply append an et al., then stop iterating
            if author_index == 5:
                append_new_text(citation_div, 'et al.', join_str='')
                break
            else:
                #Check if the author contrib has a collab
                #This will signify unique behavior
                if len(author.collab) > 0:  #Author element is a collab
                    #As best as I can tell from PLoS' reference implementation
                    #The thing to do is append all below, but remove any child
                    #contrib-group elements
                    collab = deepcopy(author.collab[0])
                    for contrib_group in collab.contrib_group:
                        remove(contrib_group)
                    append_all_below(citation_div, collab.node, join_str='')
                #If the author is not a collab, do this instead
                else:  # Author element is not a collab
                    name = author.name[0]
                    #Note that this does not support eastern names
                    #Grab the surname information
                    append_new_text(citation_div, name.surname.text, join_str='')
                    #Make initials from the given-name information
                    if name.given_names is not None:
                        #Add a space
                        append_new_text(citation_div, ' ', join_str='')
                        #Split by whitespace and take first character
                        given_initials = [i[0] for i in name.given_names.text.split() if i]
                        for initial in given_initials:
                            append_new_text(citation_div, initial, join_str='')
                    #If there is a suffix, add its text, but don't include the
                    #trailing period if there is one
                    if name.suffix is not None:
                        #Add a space
                        append_new_text(citation_div, ' ', join_str='')
                        suffix_text = name.suffix.text
                        #Check for the trailing period
                        if suffix_text[-1] == '.':
                            suffix_text = suffix_text[:-1]
                        append_new_text(citation_div, suffix_text, join_str='')
                #If this is not the last author to be added, add a ", "
                #This is satisfied by being less than the 6th author, or less
                #than the length of the author_list - 1
                if author_index < 5 or author_index < len(author_list) -1:
                    append_new_text(citation_div, ', ', join_str='')
        #Add Publication Year to the citation
        #Find pub-date elements, use pub-type=collection, or else pub-type=ppub
        for pub_date in self.article.metadata.front.article_meta.pub_date:
            #pub_year = '1337'
            if 'pub-type' not in pub_date.attrs:
                continue
            elif pub_date.attrs['pub-type'] == 'collection':
                pub_year = pub_date.year.text
                break
            elif pub_date.attrs['pub-type'] == 'ppub':
                pub_year = pub_date.year.text
        append_new_text(citation_div, ' ({0}) '.format(pub_year), join_str='')
        #Add the Article Title to the Citation
        #As best as I can tell from the reference implementation, they
        #serialize the article title to text-only, and expunge redundant spaces
        #This might need later review
        article_title = self.article.metadata.front.article_meta.title_group.article_title.node
        article_title_text = str(etree.tostring(article_title, method='text', encoding='utf-8'), encoding='utf-8')
        normalized = ' '.join(article_title_text.split())  # Remove redundant whitespace
        #Add a period unless there is some other valid punctuation
        if normalized[-1] not in '.?!':
            normalized += '.'
        append_new_text(citation_div, normalized + ' ', join_str='')
        #Add the article's journal name using the journal-id of type "nlm-ta"
        for journal_id in self.article.metadata.front.journal_meta.journal_id:
            if 'journal-id-type' not in journal_id.attrs:
                continue
            elif journal_id.attrs['journal-id-type'] == 'nlm-ta':
                journal = journal_id.text
        append_new_text(citation_div, journal + ' ', join_str='')
        #Add the article's volume, issue, and elocation_id  values
        volume = self.article.metadata.front.article_meta.volume.text
        issue = self.article.metadata.front.article_meta.issue.text
        elocation_id = self.article.metadata.front.article_meta.elocation_id.text
        stuff = '{0}({1}): {2}. '.format(volume, issue, elocation_id)
        append_new_text(citation_div, stuff, join_str='')
        append_new_text(citation_div, 'doi:{0}'.format(self.article.doi), join_str='')

        return citation_div

    def make_article_info_editors(self, editors, article_info_div):
        if not editors:  # No editors
            return None

        editors_div = etree.SubElement(article_info_div, 'div')
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
                append_new_text(editors_div, '; ', join_str='')

            if len(editor.anonymous) > 0:
                append_new_text(editors_div, 'Anonymous', join_str='')
            elif len(editor.collab) > 0:
                append_all_below(editors_div, editor.collab[0].node)
            else:
                name = editor.name[0]  # Work with only first name listed
                surname = name.surname.text
                if name.given_names is not None:
                    name_text = ' '.join([name.given_names.text, surname])
                else:
                    name_text = surname
                append_new_text(editors_div, name_text)

            for xref in editor.xref:
                if xref.attrs['ref-type'] == 'aff':
                    ref_id = xref.attrs['rid']
                    for aff in self.article.metadata.front.article_meta.aff:
                        if aff.attrs['id'] == ref_id:
                            if len(aff.addr_line) > 0:
                                addr = aff.addr_line[0].node
                                append_new_text(editors_div, ', ')
                                append_all_below(editors_div, addr)
                            else:
                                append_new_text(editors_div, ', ')
                                append_all_below(editors_div, aff.node)

    def make_article_info_dates(self):
        """
        Makes the section containing important dates for the article: typically
        Received, Accepted, and Published.
        """
        dates_div = etree.Element('div', {'id': 'article-dates'})

        if self.article.metadata.front.article_meta.history is not None:
            dates = self.article.metadata.front.article_meta.history.date
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
            append_new_text(dates_div, formatted_date_string+'; ')
        if accepted is not None:  # Optional
            b = etree.SubElement(dates_div, 'b')
            b.text = 'Accepted: '
            formatted_date_string = self.format_date_string(accepted)
            append_new_text(dates_div, formatted_date_string+'; ')
        #Published date is required
        for pub_date in self.article.metadata.front.article_meta.pub_date:
            if pub_date.attrs['pub-type'] == 'epub':
                b = etree.SubElement(dates_div, 'b')
                b.text = 'Published: '
                formatted_date_string = self.format_date_string(pub_date)
                append_new_text(dates_div, formatted_date_string)
                break

        return dates_div

    def make_article_info_copyright(self, article_info_div):
        """
        Makes the copyright section for the ArticleInfo. For PLoS, this means
        handling the information contained in the metadata <permissions>
        element.
        """
        permissions = self.article.metadata.front.article_meta.permissions
        if permissions is None:  # Article contains no permissions element
            return
        copyright_div = etree.SubElement(article_info_div, 'div', {'id': 'copyright'})
        cp_bold = etree.SubElement(copyright_div, 'b')
        cp_bold.text = 'Copyright: '
        copyright_string = '\u00A9 '
        if len(permissions.copyright_holder) > 0:
            copyright_string += all_text(permissions.copyright_holder[0].node)
            copyright_string += '. '
        if len(permissions.license) > 0:  # I'm assuming only one license
            #Taking only the first license_p element
            license_p = permissions.license[0].license_p[0]
            #I expect to see only text in the
            copyright_string += all_text(license_p.node)
        append_new_text(copyright_div, copyright_string)

    def make_article_info_funding(self, article_info_div):
        """
        Creates the element for declaring Funding in the article info.
        """
        funding_group = self.article.metadata.front.article_meta.funding_group
        if len(funding_group) == 0:
            return
        funding_div = etree.SubElement(article_info_div, 'div')
        funding_div.attrib['id'] = 'funding'
        funding_b = etree.SubElement(funding_div, 'b')
        funding_b.text = 'Funding: '
        #As far as I can tell, PLoS only uses one funding-statement
        funding_statement = funding_group[0].funding_statement[0]
        append_all_below(funding_div, funding_statement.node)

    def make_article_info_competing_interests(self, article_info_div):
        """
        Creates the element for declaring competing interests in the article
        info.
        """
        #Check for author-notes
        author_notes = self.article.metadata.front.article_meta.author_notes
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
        conflict_div = etree.SubElement(article_info_div, 'div')
        conflict_div.attrib['id'] = 'conflict'
        conflict_b = etree.SubElement(conflict_div, 'b')
        conflict_b.text = 'Competing Interests: '
        #Grab the first paragraph in the fn element
        fn_p = conflict.node.find('p')
        if fn_p is not None:
            #Add all of its children to the conflict div
            append_all_below(conflict_div, fn_p)

    def make_article_info_correspondences(self, article_info_div):
        """
        Articles generally provide a first contact, typically an email address
        for one of the authors. This will supply that content.
        """
        #Check for author-notes
        author_notes = self.article.metadata.front.article_meta.author_notes
        if author_notes is None:  # skip if not found
            return
        #Check for correspondences
        correspondence = author_notes.corresp
        if len(correspondence) == 0:  # Return since no correspondence found
            return
        corresp_div = etree.SubElement(article_info_div, 'div', {'id': 'correspondence'})
        for corresp in correspondence:
            corresp_sub_div = etree.SubElement(corresp_div, 'div')
            corresp_sub_div.attrib['id'] = corresp.node.attrib['id']
            append_all_below(corresp_sub_div, corresp.node)

    def make_article_info_footnotes_other(self, article_info_div):
        """
        This will catch all of the footnotes of type 'other' in the <fn-group>
        of the <back> element.
        """
        #Check for back, skip if it doesn't exist
        if self.article.metadata.back is None:
            return
        #Check for back fn-groups, skip if empty
        fn_groups = self.article.metadata.back.fn_group
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
            other_fn_div = etree.SubElement(article_info_div,
                                            'div',
                                            {'class': 'back-fn-other'})
        for other_fn in other_fns:
            append_all_below(other_fn_div, other_fn.node)

    @Publisher.maker2
    @Publisher.maker3
    def make_back_matter(self):
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

        body = self.main.getroot().find('body')
        if self.article.metadata.back is None:
            return
        #The following things are ordered in such a way to adhere to what
        #appears to be a consistent presentation order for PLoS
        #Acknowledgments
        body.append(self.make_back_acknowledgments())
        #Author Contributions
        self.make_back_author_contributions(body)
        #Glossaries
        self.make_back_glossary(body)
        #Notes
        self.make_back_notes(body)

    @Publisher.maker2
    @Publisher.maker3
    def move_back_boxed_texts(self):
        """
        The only intended use for this function is to patch a problem seen in
        at least one PLoS article (journal.pgen.0020002). This will move any
        <boxed-text> elements over to the receiving element, which is probably
        the main body.
        """
        body = self.main.getroot().find('body')
        if self.article.metadata.back is None:
            return
        back_boxed_texts = self.article.metadata.back.node.findall('.//boxed-text')
        if len(back_boxed_texts) == 0:
            return
        for back_boxed_text in back_boxed_texts:
            body.append(back_boxed_text)

    def make_back_acknowledgments(self):
        """
        The <ack> is an important piece of back matter information, and will be
        including immediately after the main text.

        This element should only occur once, optionally, for PLoS, if a need
        becomes known, then multiple instances may be supported.
        """
        if len(self.article.metadata.back.ack) == 0:
            return
        #Take a copy of the first ack element, using its xml form
        ack = deepcopy(self.article.metadata.back.ack[0].node)
        #Modify the tag to div
        ack.tag = 'div'
        #Give it an id
        ack.attrib['id'] = 'acknowledgments'
        #Give it a title element--this is not an OPS element but doing so will
        #allow it to later be depth-formatted by self.convert_div_titles()
        ack_title = etree.Element('title')
        ack_title.text = 'Acknowledgments'
        ack.insert(0, ack_title)  # Make it the first element
        return ack

    def make_back_author_contributions(self, body):
        """
        Though this goes in the back of the document with the rest of the back
        matter, it is not an element found under <back>.

        I don't expect to see more than one of these. Compare this method to
        make_article_info_competing_interests()
        """
        #Check for author-notes
        author_notes = self.article.metadata.front.article_meta.author_notes
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
        remove_all_attributes(author_contrib)
        author_contrib.tag = 'div'
        author_contrib.attrib['id'] = 'author-contributions'
        #Give it a title element--this is not an OPS element but doing so will
        #allow it to later be depth-formatted by self.convert_div_titles()
        contributions_title = etree.Element('title')
        contributions_title.text = 'Author Contributions'
        author_contrib.insert(0, contributions_title)
        #Append the modified copy of the author contribution fn to receiving_el
        body.append(author_contrib)

    def make_back_glossary(self, body):
        """
        Glossaries are a fairly common item in papers for PLoS, but it also
        seems that they are rarely incorporated into the PLoS web-site or PDF
        formats. They are included in the ePub output however because they are
        helpful and because we can.
        """
        #Check if self.back exists
        glossaries = self.article.metadata.back.glossary
        if len(glossaries) == 0:
            return
        for glossary in glossaries:
            glossary_copy = deepcopy(glossary.node)
            glossary_copy.tag = 'div'
            glossary_copy.attrib['class'] = 'back-glossary'
            body.append(glossary_copy)

    def make_back_notes(self, body):
        """
        The notes element in PLoS articles can be employed for posting notices
        of corrections or adjustments in proof. The <notes> element has a very
        diverse content model, but PLoS practice appears to be fairly
        consistent: a single <sec> containing a <title> and a <p>
        """
        all_notes = self.article.metadata.back.notes
        if len(all_notes) == 0:
            return
        for notes in all_notes:
            notes_sec = deepcopy(notes.sec[0].node)
            notes_sec.tag = 'div'
            notes_sec.attrib['class'] = 'back-notes'
            body.append(notes_sec)

    @Publisher.special2
    @Publisher.special3
    def convert_disp_quote_elements(self):
        """
        Extract or extended quoted passage from another work, usually made
        typographically distinct from surrounding text

        <disp-quote> elements have a relatively complex content model, but PLoS
        appears to employ either <p>s or <list>s.
        """
        body = self.main.getroot().find('body')
        for disp_quote in body.findall('.//disp-quote'):
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
            #This is a fix for odd articles with <p>s outside of <caption>
            #See journal.pctr.0020006, PLoS themselves fail to format this for
            #the website, though the .pdf is good
            #It should be noted that journal.pctr.0020006 does not pass
            #validation because it places a <p> before a <caption>
            #By placing this at the end of the method, it conforms to the spec
            #by expecting such p tags after caption. This causes a hiccup in
            #the rendering for journal.pctr.0020006, but it's better than
            #skipping the data entirely AND it should also work for conforming
            #articles.
            for paragraph in supplementary.findall('p'):
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
                    continue
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
            graphic.attrib['alt'] = 'unowned-graphic'
            ns_xlink_href = element_methods.ns_format(graphic, 'xlink:href')
            if ns_xlink_href in graphic.attrib:
                xlink_href = graphic.attrib[ns_xlink_href]
                file_name = xlink_href.split('.')[-1] + '.png'
                img_dir = 'images-' + self.doi_frag
                img_path = '/'.join([img_dir, file_name])
                graphic.attrib['src'] = img_path
            element_methods.remove_all_attributes(graphic, exclude=['id', 'class', 'alt', 'src'])

pub_class = PLoS
