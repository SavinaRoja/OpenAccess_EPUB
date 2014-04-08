#Standard Library modules
import os
from collections import namedtuple
import logging
import sys

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub.publisher import Publisher
from openaccess_epub.utils.element_methods import all_text, serialize

contributor_tuple = namedtuple('Contributor', 'name, role, file_as')
date_tuple = namedtuple('Date', 'year, month, day, event')
identifier_tuple = namedtuple('Identifier', 'value, scheme')

class PLoS(Publisher):
    def __init__(self):
        super(PLoS, self).__init__()
        self.epub2_support = True
        self.epub3_support = True

    def nav_contributors(self, article):
        contributor_list = []
        for contrib_group in article.metadata.front.article_meta.contrib_group:
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

    def nav_title(self, article):
        #Serializes the article-title element, since it is not just text
        article_title = article.metadata.front.article_meta.title_group.article_title.node
        return serialize(article_title, strip=True)

    def package_identifier(self, article):
        #Returning the DOI
        return identifier_tuple(article.doi, 'DOI')

    def package_language(self, article):
        #All PLoS articles are published in English
        return ['en']

    def package_title(self, article):
        #Sends the same result as for the Navigation Document
        return self.nav_title(article)

    def package_contributor(self, article):
        contributor_list = []
        for contrib_group in article.metadata.front.article_meta.contrib_group:
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

    def package_publisher(self, article):
        return 'Public Library of Science'

    def package_description(self, article):
        """
        Given an Article class instance, this is responsible for returning an
        article description. For this method I have taken the approach of
        serializing the article's first abstract, if it has one. This results
        in 0 or 1 descriptions per article.
        """
        abstract = article.metadata.front.article_meta.abstract
        abst_text = serialize(abstract[0].node, strip=True) if abstract else ''
        return abst_text

    def package_date(self, article):
        #This method looks specifically to locate the dates of PLoS acceptance
        #and publishing online
        date_list = []
        #Creation is a Dublin Core event value: I interpret it as the date of acceptance
        history = article.metadata.front.article_meta.history
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
        pub_dates = article.metadata.front.article_meta.pub_date
        for pub_date in pub_dates:
            if pub_date.attrs['pub-type'] == 'epub':
                date_list.append(date_tuple(pub_date.year.text,
                                            pub_date.month.text,
                                            pub_date.day.text,
                                            'copyrighted'))
        return date_list

    def package_subject(self, article):
        #Concerned only with kwd elements, not compound-kwd elements
        #Basically just compiling a list of their serialized text
        subject_list = []
        kwd_groups = article.metadata.front.article_meta.kwd_group
        for kwd_group in kwd_groups:
            for kwd in kwd_group.kwd:
                subject_list.append(serialize(kwd.node))
        return subject_list

    def package_rights(self, article):
        #Perhaps we could just return a static string if everything in PLoS is
        #published under the same license. But this inspects the file
        rights = article.metadata.front.article_meta.permissions.license
        return serialize(rights[0].node)

pub_class = PLoS
