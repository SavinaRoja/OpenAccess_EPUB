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
        ##Creation of the Authors
        list_of_authors = self.get_authors_list()
        heading_div.append(self.make_heading_authors(list_of_authors))
        ##Creation of the Authors Affiliations text
        self.make_heading_affiliations(heading_div)
        ##Creation of the Abstract content for the Heading
        #self.make_heading_abstracts(heading_div)

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
        #Make and append a new element to the passed receiving_node
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
        for contrib_group in self.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if contrib.attrs['contrib-type'] == 'editor':
                    editors_list.append(contrib)
        return editors_list

pub_class = PLoS
