# -*- coding: utf-8 -*-

"""
"""

#Standard Library modules
import logging
from copy import copy, deepcopy

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

log = logging.getLogger('openaccess_epub.publisher.plos')


class PLoS(Publisher):
    def __init__(self, article):
        super(PLoS, self).__init__(article)
        self.epub2_support = True
        self.epub3_support = True

    def get_contrib_names(self, contrib):
        """
        Returns an appropriate Name and File-As-Name for a contrib element.

        This code was refactored out of nav_contributors and
        package_contributors to provide a single definition point for a common
        job. This is a useful utility that may be well-employed for other
        publishers as well.
        """
        collab = contrib.find('collab')
        anon = contrib.find('anonymous')
        if collab is not None:
            proper_name = serialize(collab, strip=True)
            file_as_name = proper_name
        elif anon is not None:
            proper_name = 'Anonymous'
            file_as_name = proper_name
        else:
            name = contrib.find('name')
            surname = name.find('surname').text
            given = name.find('given-names')
            if given is not None:
                if given.text:  # Sometimes these tags are empty
                    proper_name = ' '.join([surname, given.text])
                    #File-as name is <surname>, <given-initial-char>
                    file_as_name = ', '.join([surname, given.text[0]])
                else:
                    proper_name = surname
                    file_as_name = proper_name
            else:
                proper_name = surname
                file_as_name = proper_name
        return proper_name, file_as_name

    def nav_contributors(self):
        contributor_list = []
        authors = self.article.root.xpath("../front/article-meta/contrib-group/contrib[@contrib-type='author']")
        for author in authors:
            author_name, author_file_as_name = self.get_contrib_names(author)
            contributor_list.append(contributor_tuple(author_name,
                                                      'author',
                                                      author_file_as_name))
        return contributor_list

    def nav_title(self):
        #Serializes the article-title element, since it is not just text
        #Why does this need the leading double slash?
        title = self.article.root.xpath('./front/article-meta/title-group/article-title')
        return serialize(title[0], strip=True)

    def package_identifier(self):
        #Returning the DOI
        return identifier_tuple(self.article.doi, 'DOI')

    def package_language(self):
        #All PLoS articles are published in English
        return ['en']

    def package_title(self):
        #Sends the same result as for the Navigation Document
        return self.nav_title()

    def package_contributors(self):
        contributor_list = []
        authors = self.article.root.xpath("./front/article-meta/contrib-group/contrib[@contrib-type='author']")
        editors = self.article.root.xpath("./front/article-meta/contrib-group/contrib[@contrib-type='editor']")
        for author in authors:
            author_name, author_file_as_name = self.get_contrib_names(author)
            contributor_list.append(contributor_tuple(author_name,
                                                      'aut',
                                                      author_file_as_name))
        for editor in editors:
            editor_name, editor_file_as_name = self.get_contrib_names(author)
            contributor_list.append(contributor_tuple(editor_name,
                                                      'edt',
                                                      editor_file_as_name))
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
        abstract = self.article.root.xpath('./front/article-meta/abstract')
        return serialize(abstract[0], strip=True) if abstract else None

    def package_date(self):
        date_list = []
        #These terms come from the EPUB/dublincore spec
        accepted = self.article.root.xpath('./front/article-meta/history/date[@date-type=\'accepted\']')
        submitted = self.article.root.xpath('./front/article-meta/history/date[@date-type=\'received\']')
        copyrighted = self.article.root.xpath('./front/article-meta/pub-date[@pub-type=\'epub\']')
        for event, el_list in (('accepted', accepted),
                              ('submitted', submitted),
                              ('copyrighted', copyrighted)):
            if not el_list:
                continue
            dt = self.date_tuple_from_date(el_list[0], event)
            date_list.append(dt)
            #el = el_list[0]
            #year = el.find('year')
            #month = el.find('month')
            #day = el.find('day')
            #season = el.find('season')
            #year = year.text
            #month = month.text if month is not None else ''
            #day = day.text if day is not None else ''
            #season = season.text if season is not None else ''
            #date_list.append(date_tuple(year, month, day, season, event))
        return date_list

    def package_subject(self):
        #Concerned only with kwd elements, not compound-kwd elements
        #Basically just compiling a list of their serialized text
        subject_list = []
        for kwd_grp in self.article.root.xpath('./front/article-meta/kwd-group'):
            for kwd in kwd_group.findall('kwd'):
                subject_list.append(serialize(kwd))
        return subject_list

    def package_rights(self):
        #Perhaps we could just return a static string if everything in PLoS is
        #published under the same license. But this inspects the file
        rights = self.article.root.xpath('./front/article-meta/permissions/license')
        if rights:
            return serialize(rights[0])
        else:
            return None

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
        authors = self.article.root.xpath("./front/article-meta/contrib-group/contrib[@contrib-type='author']")
        heading_div.append(self.make_heading_authors(authors))
        #Creation of the Authors Affiliations text
        self.make_heading_affiliations(heading_div)
        #Creation of the Abstract content for the Heading
        self.make_heading_abstracts(heading_div)

    def heading_title(self):
        """
        Makes the Article Title for the Heading.

        Metadata element, content derived from FrontMatter
        """
        art_title = self.article.root.xpath('./front/article-meta/title-group/article-title')[0]
        article_title = deepcopy(art_title)
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
            collab = author.find('collab')
            anon = author.find('anon')
            if collab is not None:
                append_all_below(author_element, collab)
            elif anon is not None:  # If anonymous, just add "Anonymous"
                append_new_text(author_element, 'Anonymous')
            else:  # Author is neither Anonymous or a Collaboration
                author_name, _ = self.get_contrib_names(author)
                append_new_text(author_element, author_name)
            #TODO: Handle author footnote references, also put footnotes in the ArticleInfo
            #Example: journal.pbio.0040370.xml
            first = True
            for xref in author.xpath("./xref[@ref-type='corresp' or @ref-type='aff']"):
                _sup = xref.find('sup')
                sup_text = all_text(_sup) if _sup is not None else ''
                auth_sup = etree.SubElement(author_element, 'sup')
                sup_link = etree.SubElement(auth_sup,
                                            'a',
                                            {'href': self.main_fragment.format(xref.attrib['rid'])})
                sup_link.text = sup_text
                if first:
                    first = False
                else:
                    append_new_text(auth_sup, ', ', join_str='')
            #for xref in author.findall('xref'):
                #if xref.attrs['ref-type'] in ['corresp', 'aff']:

                    #try:
                        #sup_element = xref.sup[0].node
                    #except IndexError:
                        #sup_text = ''
                    #else:
                        #sup_text = all_text(sup_element)
                    #new_sup = etree.SubElement(author_element, 'sup')
                    #sup_link = etree.SubElement(new_sup, 'a')
                    #sup_link.attrib['href'] = self.main_fragment.format(xref.attrs['rid'])
                    #sup_link.text = sup_text
                    #if first:
                        #first = False
                    #else:
                        #new_sup.text = ','
        return author_element

    def make_heading_affiliations(self, heading_div):
        """
        Makes the content for the Author Affiliations, displays after the
        Authors segment in the Heading.

        Metadata element, content derived from FrontMatter
        """
        #Get all of the aff element tuples from the metadata
        affs = self.article.root.xpath('./front/article-meta/aff')
        #Create a list of all those pertaining to the authors
        author_affs = [i for i in affs if 'aff' in i.attrib['id']]
        #Count them, used for formatting
        if len(author_affs) == 0:
            return None
        else:
            affs_list = etree.SubElement(heading_div,
                                         'ul',
                                         {'id': 'affiliations',
                                          'class': 'simple'})

        for aff in author_affs:
            #Create a span element to accept extracted content
            aff_item = etree.SubElement(affs_list, 'li')
            aff_item.attrib['id'] = aff.attrib['id']
            #Get the first label node and the first addr-line node
            label = aff.find('label')
            addr_line = aff.find('addr-line')
            if label is not None:
                bold = etree.SubElement(aff_item, 'b')
                bold.text = all_text(label) + ' '
            if addr_line is not None:
                append_new_text(aff_item, all_text(addr_line))
            else:
                append_new_text(aff_item, all_text(aff))
            #if len(aff.label) > 0:
                #label = aff.label[0].node
                #label_text = all_text(label)
                #bold = etree.SubElement(aff_item, 'b')
                #bold.text = label_text + ' '
            #if len(aff.addr_line) > 0:
                #addr_line = aff.addr_line[0].node
                #append_new_text(aff_item, all_text(addr_line))
            #else:
                #append_new_text(aff_item, all_text(aff))

    def make_heading_abstracts(self, heading_div):
        """
        An article may contain data for various kinds of abstracts. This method
        works on those that are included in the Heading. This is displayed
        after the Authors and Affiliations.

        Metadata element, content derived from FrontMatter
        """
        for abstract in self.article.root.xpath('./front/article-meta/abstract'):
            #Make a copy of the abstract
            abstract_copy = deepcopy(abstract)
            abstract_copy.tag = 'div'
            #Abstracts are a rather diverse bunch, keep an eye on them!
            title_text = abstract_copy.xpath('./title[1]/text()')
            for title in abstract_copy.findall('.//title'):
                remove(title)
            #Create a header for the abstract
            abstract_header = etree.Element('h2')
            remove_all_attributes(abstract_copy)
            #Set the header text and abstract id according to abstract type
            abstract_type = abstract.attrib.get('abstract-type')
            log.debug('Handling Abstrace of with abstract-type="{0}"'.format(abstract_type))
            if abstract_type == 'summary':
                abstract_header.text = 'Author Summary'
                abstract_copy.attrib['id'] = 'author-summary'
            elif abstract_type == 'editors-summary':
                abstract_header.text = 'Editors\' Summary'
                abstract_copy.attrib['id'] = 'editor-summary'
            elif abstract_type == 'synopsis':
                abstract_header.text = 'Synopsis'
                abstract_copy.attrib['id'] = 'synopsis'
            elif abstract_type == 'alternate':
                #Right now, these will only be included if there is a title to
                #give it
                if title_text:
                    abstract_header.text= title_text[0]
                    abstract_copy.attrib['id'] = 'alternate'
                else:
                    continue
            elif abstract_type is None:
                abstract_header.text = 'Abstract'
                abstract_copy.attrib['id'] = 'abstract'
            elif abstract_type == 'toc':  # We don't include these
                continue
            else:  # Warn about these, then skip
                log.warning('No handling for abstract-type="{0}"'.format(abstract_type))
                continue
                #abstract_header.text = abstract_type
                #abstract_copy.attrib['id'] = abstract_type
            heading_div.append(abstract_header)
            heading_div.append(abstract_copy)

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
        editors = self.article.root.xpath("./front/article-meta/contrib-group/contrib[@contrib-type='editor']")
        self.make_article_info_editors(editors, article_info_div)
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
        authors = self.article.root.xpath("./front/article-meta/contrib-group/contrib[@contrib-type='author']")
        for author in authors:
            author_index = authors.index(author)
            #At the 6th author, simply append an et al., then stop iterating
            if author_index == 5:
                append_new_text(citation_div, 'et al.', join_str='')
                break
            else:
                #Check if the author contrib has a collab
                collab = author.find('collab')
                if collab is not None:
                    collab_copy = deepcopy(collab)
                    for contrib_group in collab_copy.findall('contrib_group'):
                        remove(contrib_group)
                    append_all_below(citation_div, collab, join_str='')
                else:  # Author element is not a collab
                    name = author.find('name')
                    #Note that this does not support eastern names
                    #Grab the surname information
                    surname = name.find('surname')
                    given_names = name.find('given-names')
                    suffix = name.find('suffix')
                    append_new_text(citation_div, surname.text, join_str='')
                    #Make initials from the given-name information
                    if given_names is not None:
                        #Add a space
                        append_new_text(citation_div, ' ', join_str='')
                        #Split by whitespace and take first character
                        given_initials = [i[0] for i in given_names.text.split() if i]
                        for initial in given_initials:
                            append_new_text(citation_div, initial, join_str='')
                    #If there is a suffix, add its text, but don't include the
                    #trailing period if there is one
                    if suffix is not None:
                        #Add a space
                        append_new_text(citation_div, ' ', join_str='')
                        suffix_text = suffix.text
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
        d = './front/article-meta/pub-date'
        coll = self.article.root.xpath(d + "[@pub-type='collection']")
        ppub = self.article.root.xpath(d + "[@pub-type='ppub']")
        if coll:
            pub_year = coll[0].find('year').text
        elif ppub:
            pub_year = ppub[0].find('year').text
        append_new_text(citation_div, ' ({0}) '.format(pub_year), join_str='')
        #Add the Article Title to the Citation
        #As best as I can tell from the reference implementation, they
        #serialize the article title to text-only, and expunge redundant spaces
        #This might need later review
        article_title = self.article.root.xpath('./front/article-meta/title-group/article-title')[0]
        article_title_text = serialize(article_title)
        normalized = ' '.join(article_title_text.split())  # Remove redundant whitespace
        #Add a period unless there is some other valid punctuation
        if normalized[-1] not in '.?!':
            normalized += '.'
        append_new_text(citation_div, normalized + ' ', join_str='')
        #Add the article's journal name using the journal-id of type "nlm-ta"
        journal = self.article.root.xpath("./front/journal-meta/journal-id[@journal-id-type='nlm-ta']")
        append_new_text(citation_div, journal[0].text + ' ', join_str='')
        #Add the article's volume, issue, and elocation_id  values
        volume = self.article.root.xpath('./front/article-meta/volume')[0].text
        issue = self.article.root.xpath('./front/article-meta/issue')[0].text
        elocation_id = self.article.root.xpath('./front/article-meta/elocation-id')[0].text
        form = '{0}({1}): {2}. '.format(volume, issue, elocation_id)
        append_new_text(citation_div, form, join_str='')
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
            name, _ = self.get_contrib_names(editor)
            if first:
                first = False
            else:
                append_new_text(editors_div, '; ', join_str='')

            collab = editor.find('collab')
            if collab:
                append_all_below(editors_div, collab[0])
            else:
                append_new_text(editors_div, name)

            for affref in editor.xpath("./xref[@ref-type='aff']"):
                for aff in self.article.root.xpath('./front/article-meta/aff'):
                    if aff.attrib['id'] == affref.attrib['rid']:
                        addr_line = aff.find('addr-line')
                        if addr_line is not None:
                            append_new_text(editors_div, ', ')
                            append_all_below(editors_div, addr_line)
                        else:
                            append_new_text(editors_div, ', ')
                            append_all_below(editors_div, aff)

    def date_tuple_from_date(self, date_el, event):
        year = date_el.find('year')
        month = date_el.find('month')
        day = date_el.find('day')
        season = date_el.find('season')
        year = year.text
        month = month.text if month is not None else ''
        day = day.text if day is not None else ''
        season = season.text if season is not None else ''
        return date_tuple(year, month, day, season, event)

    def make_article_info_dates(self):
        """
        Makes the section containing important dates for the article: typically
        Received, Accepted, and Published.
        """
        dates_div = etree.Element('div', {'id': 'article-dates'})

        d = './front/article-meta/history/date'
        received = self.article.root.xpath(d + "[@date-type='received']")
        accepted = self.article.root.xpath(d + "[@date-type='accepted']")
        if received:
            b = etree.SubElement(dates_div, 'b')
            b.text = 'Received: '
            dt = self.date_tuple_from_date(received[0], 'Received')
            formatted_date_string = self.format_date_string(dt)
            append_new_text(dates_div, formatted_date_string + '; ')
        if accepted:
            b = etree.SubElement(dates_div, 'b')
            b.text = 'Accepted: '
            dt = self.date_tuple_from_date(accepted[0], 'Accepted')
            formatted_date_string = self.format_date_string(dt)
            append_new_text(dates_div, formatted_date_string + '; ')
        #Published date is required
        pub_date = self.article.root.xpath("./front/article-meta/pub-date[@pub-type='epub']")[0]
        b = etree.SubElement(dates_div, 'b')
        b.text = 'Published: '
        dt = self.date_tuple_from_date(pub_date, 'Published')
        formatted_date_string = self.format_date_string(dt)
        append_new_text(dates_div, formatted_date_string)

        return dates_div

    def make_article_info_copyright(self, article_info_div):
        """
        Makes the copyright section for the ArticleInfo. For PLoS, this means
        handling the information contained in the metadata <permissions>
        element.
        """
        perm = self.article.root.xpath('./front/article-meta/permissions')
        if not perm:
            return
        copyright_div = etree.SubElement(article_info_div, 'div', {'id': 'copyright'})
        cp_bold = etree.SubElement(copyright_div, 'b')
        cp_bold.text = 'Copyright: '
        copyright_string = '\u00A9 '
        copyright_holder = perm[0].find('copyright-holder')
        if copyright_holder is not None:
            copyright_string += all_text(copyright_holder) + '. '
        lic = perm[0].find('license')
        if lic is not None:
            copyright_string += all_text(lic.find('license-p'))
        append_new_text(copyright_div, copyright_string)

    def make_article_info_funding(self, article_info_div):
        """
        Creates the element for declaring Funding in the article info.
        """
        funding_group = self.article.root.xpath('./front/article-meta/funding-group')
        if funding_group:
            funding_div = etree.SubElement(article_info_div,
                                           'div',
                                           {'id': 'funding'})
            funding_b = etree.SubElement(funding_div, 'b')
            funding_b.text = 'Funding: '
            #As far as I can tell, PLoS only uses one funding-statement
            funding_statement = funding_group[0].find('funding-statement')
            append_all_below(funding_div, funding_statement)

    def make_article_info_competing_interests(self, article_info_div):
        """
        Creates the element for declaring competing interests in the article
        info.
        """
        #Check for author-notes
        con_expr = "./front/article-meta/author-notes/fn[@fn-type='conflict']"
        conflict = self.article.root.xpath(con_expr)
        if not conflict:
            return
        conflict_div = etree.SubElement(article_info_div,
                                        'div',
                                        {'id': 'conflict'})
        b = etree.SubElement(conflict_div, 'b')
        b.text = 'Competing Interests: '
        fn_p = conflict[0].find('p')
        if fn_p is not None:
            append_all_below(conflict_div, fn_p)

    def make_article_info_correspondences(self, article_info_div):
        """
        Articles generally provide a first contact, typically an email address
        for one of the authors. This will supply that content.
        """
        corresps = self.article.root.xpath('./front/article-meta/author-notes/corresp')
        if corresps:
            corresp_div = etree.SubElement(article_info_div,
                                           'div',
                                           {'id': 'correspondence'})
        for corresp in corresps:
            sub_div = etree.SubElement(corresp_div,
                                       'div',
                                       {'id': corresp.attrib['id']})
            append_all_below(sub_div, corresp)

    def make_article_info_footnotes_other(self, article_info_div):
        """
        This will catch all of the footnotes of type 'other' in the <fn-group>
        of the <back> element.
        """
        other_fn_expr = "./back/fn-group/fn[@fn-type='other']"
        other_fns = self.article.root.xpath(other_fn_expr)
        if other_fns:
            other_fn_div = etree.SubElement(article_info_div,
                                            'div',
                                            {'class': 'back-fn-other'})
        for other_fn in other_fns:
            append_all_below(other_fn_div, other_fn)

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
        if self.article.root.find('back') is None:
            return
        #The following things are ordered in such a way to adhere to what
        #appears to be a consistent presentation order for PLoS
        #Acknowledgments
        back_ack = self.make_back_acknowledgments()
        if back_ack is not None:
            body.append(back_ack)
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
        back = self.article.root.find('back')
        if back is None:
            return
        boxed_texts = back.xpath('.//boxed-text')
        for boxed_text in boxed_texts:
            body.append(deepcopy(boxed_text))

    def make_back_acknowledgments(self):
        """
        The <ack> is an important piece of back matter information, and will be
        including immediately after the main text.

        This element should only occur once, optionally, for PLoS, if a need
        becomes known, then multiple instances may be supported.
        """
        acks = self.article.root.xpath('./back/ack')
        if not acks:
            return
        ack = deepcopy(acks[0])
        #Modify the tag to div
        ack.tag = 'div'
        #Give it an id
        ack.attrib['id'] = 'acknowledgments'
        #Give it a title element--this is not an EPUB element but doing so will
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
        cont_expr = "./front/article-meta/author-notes/fn[@fn-type='con']"
        contribution = self.article.root.xpath(cont_expr)
        if contribution:
            author_contrib = deepcopy(contribution[0])
            remove_all_attributes(author_contrib)
            author_contrib.tag = 'div'
            author_contrib.attrib['id'] = 'author-contributions'
            #This title element will be parsed later
            title = etree.Element('title')
            title.text = 'Author Contributions'
            author_contrib.insert(0, title)
            body.append(author_contrib)

    def make_back_glossary(self, body):
        """
        Glossaries are a fairly common item in papers for PLoS, but it also
        seems that they are rarely incorporated into the PLoS web-site or PDF
        formats. They are included in the ePub output however because they are
        helpful and because we can.
        """
        for glossary in self.article.root.xpath('./back/glossary'):
            gloss_copy = deepcopy(glossary)
            gloss_copy.tag = 'div'
            gloss_copy.attrib['class'] = 'back-glossary'
            body.append(gloss_copy)

    def make_back_notes(self, body):
        """
        The notes element in PLoS articles can be employed for posting notices
        of corrections or adjustments in proof. The <notes> element has a very
        diverse content model, but PLoS practice appears to be fairly
        consistent: a single <sec> containing a <title> and a <p>
        """
        for notes in self.article.root.xpath('./back/notes'):
            notes_sec = deepcopy(notes.find('sec'))
            notes_sec.tag = 'div'
            notes_sec.attrib['class'] = 'back-notes'
            body.append(notes_sec)

    @Publisher.special2
    @Publisher.special3
    def convert_disp_formula_elements(self):
        """
        <disp-formula> elements must be converted to conforming elements
        """
        for disp in self.main.getroot().findall('.//disp-formula'):
            #find label element
            label_el = disp.find('label')
            graphic_el = disp.find('graphic')
            if graphic_el is None:  # No graphic, assume math as text instead
                text_span = etree.Element('span', {'class': 'disp-formula'})
                if 'id' in disp.attrib:
                    text_span.attrib['id'] = disp.attrib['id']
                append_all_below(text_span, disp)
                #Insert the text span before the disp-formula
                insert_before(disp, text_span)
                #If a label exists, modify and insert before text_span
                if label_el is not None:
                    label_el.tag = 'b'
                    insert_before(text_span, label_el)
                #Remove the disp-formula
                remove(disp)
                #Skip the rest, which deals with the graphic element
                continue
            #The graphic element is present
            #Create a file reference for the image
            xlink_href = ns_format(graphic_el, 'xlink:href')
            graphic_xlink_href = graphic_el.attrib[xlink_href]
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_suffix()
            img_path = '/'.join([img_dir, file_name])

            #Create the img element
            img_element = etree.Element('img', {'alt': 'A Display Formula',
                                                'class': 'disp-formula',
                                                'src': img_path})
            #Transfer the id attribute
            if 'id' in disp.attrib:
                img_element.attrib['id'] = disp.attrib['id']
            #Insert the img element
            insert_before(disp, img_element)
            #Create content for the label
            if label_el is not None:
                label_el.tag = 'b'
                insert_before(img_element, label_el)
            #Remove the old disp-formula element
            remove(disp)

    @Publisher.special2
    @Publisher.special3
    def convert_inline_formula_elements(self):
        """
        <inline-formula> elements must be converted to be conforming

        These elements may contain <inline-graphic> elements, textual content,
        or both.
        """
        for inline in self.main.getroot().findall('.//inline-formula'):
            #inline-formula elements will be modified in situ
            remove_all_attributes(inline)
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
            remove_all_attributes(inline_graphic)
            #Create a file reference for the image
            xlink_href = ns_format(inline_graphic, 'xlink:href')
            graphic_xlink_href = inline_graphic_attributes[xlink_href]
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_suffix()
            img_path = '/'.join([img_dir, file_name])
            #Set the source to the image path
            inline_graphic.attrib['src'] = img_path
            inline_graphic.attrib['class'] = 'inline-formula'
            inline_graphic.attrib['alt'] = 'An Inline Formula'

    @Publisher.special2
    @Publisher.special3
    def convert_disp_quote_elements(self):
        """
        Extract or extended quoted passage from another work, usually made
        typographically distinct from surrounding text

        <disp-quote> elements have a relatively complex content model, but PLoS
        appears to employ either <p>s or <list>s.
        """
        for disp_quote in self.main.getroot().findall('.//disp-quote'):
            if disp_quote.getparent().tag == 'p':
                elevate_element(disp_quote)
            disp_quote.tag = 'div'
            disp_quote.attrib['class'] = 'disp-quote'

    @Publisher.special2
    @Publisher.special3
    def convert_boxed_text_elements(self):
        """
        Textual material that is part of the body of text but outside the
        flow of the narrative text, for example, a sidebar, marginalia, text
        insert (whether enclosed in a box or not), caution, tip, note box, etc.

        <boxed-text> elements for PLoS appear to all contain a single <sec>
        element which frequently contains a <title> and various other content.
        This method will elevate the <sec> element, adding class information as
        well as processing the title.
        """
        for boxed_text in self.main.getroot().findall('.//boxed-text'):
            sec_el = boxed_text.find('sec')
            if sec_el is not None:
                sec_el.tag = 'div'
                title = sec_el.find('title')
                if title is not None:
                    title.tag = 'b'
                sec_el.attrib['class'] = 'boxed-text'
                if 'id' in boxed_text.attrib:
                    sec_el.attrib['id'] = boxed_text.attrib['id']
                replace(boxed_text, sec_el)
            else:
                div_el = etree.Element('div', {'class': 'boxed-text'})
                if 'id' in boxed_text.attrib:
                    div_el.attrib['id'] = boxed_text.attrib['id']
                append_all_below(div_el, boxed_text)
                replace(boxed_text, div_el)

    @Publisher.special2
    @Publisher.special3
    def convert_supplementary_material_elements(self):
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
        for supplementary in self.main.getroot().findall('.//supplementary-material'):
            #Create a div element to hold the supplementary content
            suppl_div = etree.Element('div')
            if 'id' in supplementary.attrib:
                suppl_div.attrib['id'] = supplementary.attrib['id']
            insert_before(supplementary, suppl_div)
            #Get the sub elements
            label = supplementary.find('label')
            caption = supplementary.find('caption')
            #Get the external resource URL for the supplementary information
            ns_xlink_href = ns_format(supplementary, 'xlink:href')
            xlink_href = supplementary.attrib[ns_xlink_href]
            resource_url = self.fetch_single_representation(xlink_href)
            if label is not None:
                label.tag = 'a'
                label.attrib['href'] = resource_url
                append_new_text(label, '. ', join_str='')
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
            remove(supplementary)

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
        subjournal_name = self.article.doi.split('.')[2]
        base_url = journal_urls[subjournal_name]
        #Compose the address for fetchSingleRepresentation
        resource = 'fetchSingleRepresentation.action?uri=' + item_xlink_href
        return base_url.format(resource)

    @Publisher.special2
    @Publisher.special3
    def convert_fig_elements(self):
        """
        Responsible for the correct conversion of JPTS 3.0 <fig> elements to
        EPUB xhtml. Aside from translating <fig> to <img>, the content model
        must be edited.
        """
        for fig in self.main.getroot().findall('.//fig'):
            if fig.getparent().tag == 'p':
                elevate_element(fig)
        for fig in self.main.getroot().findall('.//fig'):
            #self.convert_fn_elements(fig)
            #self.convert_disp_formula_elements(fig)
            #Find label and caption
            label_el = fig.find('label')
            caption_el = fig.find('caption')
            #Get the graphic node, this should be mandatory later on
            graphic_el = fig.find('graphic')
            #Create a file reference for the image
            xlink_href = ns_format(graphic_el, 'xlink:href')
            graphic_xlink_href = graphic_el.attrib[xlink_href]
            file_name = graphic_xlink_href.split('.')[-1] + '.png'
            img_dir = 'images-' + self.doi_suffix()
            img_path = '/'.join([img_dir, file_name])

            #Create the content: using image path, label, and caption
            img_el = etree.Element('img', {'alt': 'A Figure', 'src': img_path,
                                           'class': 'figure'})
            if 'id' in fig.attrib:
                img_el.attrib['id'] = fig.attrib['id']
            insert_before(fig, img_el)

            #Create content for the label and caption
            if caption_el is not None or label_el is not None:
                img_caption_div = etree.Element('div', {'class': 'figure-caption'})
                img_caption_div_b = etree.SubElement(img_caption_div, 'b')
                if label_el is not None:
                    append_all_below(img_caption_div_b, label_el)
                    append_new_text(img_caption_div_b, '. ', join_str='')
                if caption_el is not None:
                    caption_title = caption_el.find('title')
                    if caption_title is not None:
                        append_all_below(img_caption_div_b, caption_title)
                        append_new_text(img_caption_div_b, ' ', join_str='')
                    for each_p in caption_el.findall('p'):
                        append_all_below(img_caption_div, each_p)
                insert_before(fig, img_caption_div)

            #Remove the original <fig>
            remove(fig)

    @Publisher.special2
    @Publisher.special3
    def convert_verse_group_elements(self):
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
        for verse_group in self.main.getroot().findall('.//verse-group'):
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
                    append_all_below(new_verse_title, label)
                    remove(label)
                if title is not None:
                    append_all_below(new_verse_title, title)
                    remove(title)
                if subtitle is not None:
                    append_all_below(new_verse_title, subtitle)
                    remove(subtitle)
            for verse_line in verse_group.findall('verse-line'):
                verse_line.tag = 'p'
                verse_line.attrib['class'] = 'verse-line'

    @Publisher.special2
    @Publisher.special3
    def convert_fn_elements(self):
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
        for footnote in self.main.getroot().findall('.//fn'):
            #Use only the first paragraph
            paragraph = footnote.find('p')
            #If no paragraph, move on
            if paragraph is None:
                remove(footnote)
                continue
            #Simply remove corrected errata items
            paragraph_text = str(etree.tostring(paragraph, method='text', encoding='utf-8'), encoding='utf-8')
            if paragraph_text.startswith('Erratum') and 'Corrected' in paragraph_text:
                remove(footnote)
                continue
            #Transfer some attribute information from the fn element to the paragraph
            if 'id' in footnote.attrib:
                paragraph.attrib['id'] = footnote.attrib['id']
            if 'fn-type' in footnote.attrib:
                paragraph.attrib['class'] = 'fn-type-{0}'.footnote.attrib['fn-type']
            else:
                paragraph.attrib['class'] = 'fn'
                #Replace the
            replace(footnote, paragraph)

    @Publisher.special2
    @Publisher.special3
    def convert_list_elements(self):
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
        for list_el in self.main.getroot().findall('.//list'):
            if list_el.getparent().tag == 'p':
                elevate_element(list_el)

        #list_el is used instead of list (list is reserved)
        for list_el in self.main.getroot().findall('.//list'):
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
            remove_all_attributes(list_el, exclude=['id', 'class'])

    @Publisher.special2
    @Publisher.special3
    def convert_def_list_elements(self):
        """
        A list in which each item consists of two parts: a word, phrase, term,
        graphic, chemical structure, or equation paired with one of more
        descriptions, discussions, explanations, or definitions of it.

        <def-list> elements are lists of <def-item> elements which are in turn
        composed of a pair of term (<term>) and definition (<def>). This method
        will convert the <def-list> to a classed <div> with a styled format
        for the terms and definitions.
        """
        for def_list in self.main.getroot().findall('.//def-list'):
            #Remove the attributes, excepting id
            remove_all_attributes(def_list, exclude=['id'])
            #Modify the def-list element
            def_list.tag = 'div'
            def_list.attrib['class'] = 'def-list'
            for def_item in def_list.findall('def-item'):
                #Get the term being defined, modify it
                term = def_item.find('term')
                term.tag = 'p'
                term.attrib['class']= 'def-item-term'
                #Insert it before its parent def_item
                insert_before(def_item, term)
                #Get the definition, handle missing with a warning
                definition = def_item.find('def')
                if definition is None:
                    log.warning('Missing def element in def-item')
                    remove(def_item)
                    continue
                #PLoS appears to consistently place all definition text in a
                #paragraph subelement of the def element
                def_para = definition.find('p')
                def_para.attrib['class'] = 'def-item-def'
                #Replace the def-item element with the p element
                replace(def_item, def_para)

    @Publisher.special2
    @Publisher.special3
    def convert_ref_list_elements(self):
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
        for ref_list in self.main.getroot().findall('.//ref-list'):
            remove_all_attributes(ref_list)
            ref_list.tag = 'div'
            ref_list.attrib['class'] = 'ref-list'
            label = ref_list.find('label')
            if label is not None:
                label.tag = 'h3'
            for ref in ref_list.findall('ref'):
                ref_p = etree.Element('p')
                ref_p.text = str(etree.tostring(ref, method='text', encoding='utf-8'), encoding='utf-8')
                replace(ref, ref_p)

    @Publisher.special2
    @Publisher.special3
    def convert_table_wrap_elements(self):
        """
        Responsible for the correct conversion of JPTS 3.0 <table-wrap>
        elements to EPUB content.

        The 'id' attribute is treated as mandatory by this method.
        """
        for table_wrap in self.main.getroot().findall('.//table-wrap'):

            table_div = etree.Element('div', {'id': table_wrap.attrib['id']})

            label = table_wrap.find('label')
            caption = table_wrap.find('caption')
            alternatives = table_wrap.find('alternatives')
            graphic = table_wrap.find('graphic')
            table = table_wrap.find('table')
            if graphic is None:
                if alternatives is not None:
                    graphic = alternatives.find('graphic')
            if table is None:
                if alternatives is not None:
                    table = alternatives.find('table')

            #Handling the label and caption
            if label is not None and caption is not None:
                caption_div = etree.Element('div', {'class': 'table-caption'})
                caption_div_b = etree.SubElement(caption_div, 'b')
                if label is not None:
                    append_all_below(caption_div_b, label)
                if caption is not None:
                    #Find, optional, title element and paragraph elements
                    caption_title = caption.find('title')
                    if caption_title is not None:
                        append_all_below(caption_div_b, caption_title)
                    caption_ps = caption.findall('p')
                    #For title and each paragraph, give children to the div
                    for caption_p in caption_ps:
                        append_all_below(caption_div, caption_p)
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
                xlink_href = ns_format(graphic, 'xlink:href')
                graphic_xlink_href = graphic.attrib[xlink_href]
                file_name = graphic_xlink_href.split('.')[-1] + '.png'
                img_dir = 'images-' + self.doi_suffix()
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
                    div = etree.SubElement(self.tables.find('body'),
                                           'div',
                                           {'id': table_wrap.attrib['id']})

                    if label is not None:
                        bold_label = etree.SubElement(div, 'b')
                        append_all_below(bold_label, label)
                    #Add the table to the tables list
                    div.append(deepcopy(table))
                    #Also add the table's foot if it exists
                    table_wrap_foot = table_wrap.find('table-wrap-foot')
                    if table_wrap_foot is not None:
                        table_wrap_foot.tag = 'div'
                        table_wrap_foot.attrib['class'] = 'table-wrap-foot'
                        div.append(table_wrap_foot)
                    #Create a link to the html version of the table
                    html_table_link = etree.Element('a')
                    html_table_link.attrib['href'] = self.tables_fragment.format(table_wrap.attrib['id'])
                    html_table_link.text = 'Go to HTML version of this table'
                    #Add this to the table div
                    table_div.append(html_table_link)
                    remove(table)

            elif table is not None:  # Table only
                #Simply append the table to the table div
                table_div.append(table)
            elif graphic is None and table is None:
                sys.exit('Encountered table-wrap element with neither graphic nor table. Exiting.')

            #Replace the original table-wrap with the newly constructed div
            replace(table_wrap, table_div)

    @Publisher.special3
    def html5_table_modification(self):
        invalid_attrs = ['align', 'bgcolor', 'border', 'cellpadding', 'char',
                         'charoff', 'cellspacing', 'height', 'nowrap', 'rules',
                         'valign', 'width']
        for el in self.tables.xpath('//tr | //td | //th'):
            for inv_attr in invalid_attrs:
                if inv_attr in el.attrib:
                    el.attrib.pop(inv_attr)
        #TODO: Perhaps something more elaborate could be done here to translate
        #the colgroup and cols to the new HTML5 spec, keep in mind that the col
        #element "Must be used within a HTML colgroup element that doesn't have
        #a span attribute."
        #For now, I just yank em out
        for colgroup in self.tables.findall('//colgroup'):
            remove(colgroup)

    @Publisher.special2
    @Publisher.special3
    def convert_graphic_elements(self):
        """
        This is a method for the odd special cases where <graphic> elements are
        standalone, or rather, not a part of a standard graphical element such
        as a figure or a table. This method should always be employed after the
        standard cases have already been handled.
        """
        for graphic in self.main.getroot().findall('.//graphic'):
            graphic.tag = 'img'
            graphic.attrib['alt'] = 'unowned-graphic'
            ns_xlink_href = ns_format(graphic, 'xlink:href')
            if ns_xlink_href in graphic.attrib:
                xlink_href = graphic.attrib[ns_xlink_href]
                file_name = xlink_href.split('.')[-1] + '.png'
                img_dir = 'images-' + self.doi_suffix()
                img_path = '/'.join([img_dir, file_name])
                graphic.attrib['src'] = img_path
            remove_all_attributes(graphic, exclude=['id', 'class', 'alt', 'src'])

    @Publisher.maker2
    @Publisher.maker3
    def make_biblio(self):
        body = self.biblio.find('body')
        refs = self.article.root.xpath('./back/ref-list/ref')
        if refs:
            etree.SubElement(body, 'h2', {'id': 'references'})
        for ref in refs:
            #Time for a little XML butchery/cookery
            ref_copy = deepcopy(ref)

            label = ref_copy.find('label')
            year = ref_copy.xpath('./element-citation/year | nlm-citation/year')
            etal = ref_copy.xpath('./element-citation/person-group/etal | \
nlm-citation/person-group/etal')
            volume = ref_copy.xpath('./element-citation/volume | nlm-citation/volume')
            fpage = ref_copy.xpath('./element-citation/fpage | nlm-citation/fpage')
            lpage = ref_copy.xpath('./element-citation/lpage | nlm-citation/lpage')
            title = ref_copy.xpath('./element-citation/article-title | nlm-citation/article-title')

            ref_div = etree.SubElement(body, 'div', {'id': ref.attrib['id']})
            ref_p = etree.SubElement(ref_div, 'p')
            links_p = etree.SubElement(ref_div, 'p')

            if label is not None:
                b = etree.SubElement(ref_p, 'b')
                b.text = label.text
                b.tail = ' '
                if not b.text.endswith('.'):
                    b.text = b.text + '.'
                remove(label)
            if year:
                year[0].text = '({0})'.format(year[0].text)
            for name in ref_copy.iter(tag='name'):
                if name.getnext() is None:
                    continue  # This way we don't put a comma on the last name
                append_new_text(name, ',', join_str='')
            if etal:
                prev = etal[0].getprevious()
                if prev is not None:
                    prev.tail = 'et al.'
            if volume:
                volume[0].text = volume[0].text + ':'
            if fpage and lpage:
                fpage[0].text = '-'.join([fpage[0].text, lpage[0].text])
                remove(lpage[0])

            #last_name = ref_copy.xpath('./element-citation/person-group/name[last()] | ./nlm-citation/person-group/name[last()]')

            if title:
                title_text = serialize(title[0])
                pmed_href = 'http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=PubMed&cmd=Search&doptcmdl=Citation&defaultField=Title+Word&term='
                pmed_href = pmed_href + title_text.replace(' ', '+')
                pmed = etree.SubElement(links_p, 'a', {'href': pmed_href})
                pmed.text = 'PubMed/NCBI'
                pmed.tail = ' • '
                schol_href = 'http://scholar.google.com/scholar?hl=en&safe=off&q=%22{0}%22'
                schol_href = schol_href.format(title_text.replace(' ', '+'))
                schol = etree.SubElement(links_p, 'a', {'href': schol_href})
                schol.text = 'Google Scholar'

            for el in ref_copy.iter():
                append_new_text(el, ' ', join_str='')
            ref_text = serialize(ref_copy)
            while ref_text.endswith(' '):
                ref_text = ref_text[:-1]
            if not ref_text.endswith('.'):
                ref_text = ref_text + '.'



#http://dx.doi.org/10.1016/s1534-5807(03)00055-8
#http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=PubMed&cmd=Search&doptcmdl=Citation&defaultField=Title+Word&term=Wnt3a+plays+a+major+role+in+the+segmentation+clock+controlling+somitogenesis.
#http://scholar.google.com/scholar?hl=en&safe=off&q=%22Wnt3a+plays+a+major+role+in+the+segmentation+clock+controlling+somitogenesis.%22

            append_new_text(ref_p, ref_text)

    def process_named_content_tag(self, element, epub_version):
        element.tag = 'span'
        content_type = element.attrib.get('content-type')
        remove_all_attributes(element)
        if content_type is not None:
            element.attrib['class'] = content_type

pub_class = PLoS
