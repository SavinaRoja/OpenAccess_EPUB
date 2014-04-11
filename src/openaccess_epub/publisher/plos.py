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
from openaccess_epub.utils.element_methods import all_text, serialize


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
    def make_heading(self):
        body = self.main.getroot().find('body')
        heading_div = etree.Element('div')
        body.insert(0, heading_div)
        heading_div.attrib['id'] = 'Heading'
        #Creation of the title
        heading_div.append(self.heading_title())

        ##Creation of the Authors
        #list_of_authors = self.get_authors_list()
        #self.make_heading_authors(list_of_authors, heading_div)
        ##Creation of the Authors Affiliations text
        #self.make_heading_affiliations(heading_div)
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

pub_class = PLoS
