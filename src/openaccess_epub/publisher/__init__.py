# -*- coding: utf-8 -*-

"""
openaccess_epub.publisher defines abstract publisher representation and content
conversion
"""

#Standard Library modules
from collections import namedtuple
import logging

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub.utils.element_methods import serialize

log = logging.getLogger('openaccess_epub.publisher')

creator = namedtuple('Creator', 'name, role, file_as')
contributor = namedtuple('Contributor', 'name, role, file_as')
date_tup = namedtuple('Date', 'year, month, day, event')
identifier = namedtuple('Identifier', 'value, scheme')


class Publisher(object):
    """
    Meta class for publishers, sub-class per publisher to add support
    """
    def __init__(self):
        """
        The initialization of the Publisher class.
        """
        self.epub2_support = False
        self.epub3_support = False

    def pre_processing(self):
        """
        """
        pass

    def post_processing(self):
        """
        """
        pass

    def nav_contributors(self):
        """
        Returns a list of contributors to the article.

        This is is a metadata method that is only required to be defined for
        EPUB2 creation, though the `package_contributors` counterpart should
        always be present. This method returns a list of special namedtuples
        with the following specification: Contributor(name, role, file_as).
        The 'name' should be a string representing a standard reading form of
        the contributor's name. The 'role' will indicate one of the following:
        'author', 'editor', 'reviewer'. The 'file_as' will be a string
        representing a name as it would be catalogued. This method may differ
        from `package_contributors` if one desires, but it covers extra details
        so that it they can easily be the same.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        list of Contributor namedtuples
            A list of contributors, [Contributor(name, role, file_as)]

        Notes
        -----
        The Navigation Document will utilize the results of this method in the
        following manner: When making EPUB2, if Contributor.role is 'author',
        then Contributor.name will be entered as a docAuthor.
        """
        raise NotImplementedError

    def nav_title(self, article):
        """
        Returns a string for the title of the article.

        This is a required metadata method used for representing the article's
        title in the Navigation Document of the EPUB. It simply returns a string
        of the title's text. It may differ from `package_title` but it is also
        likely that these methods may be the same, in which case one may use a
        strategy to ensure they return the same results.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        title : str
            The `title` of the article being parsed for metadata.

        Notes
        -----
        This method is likely to benefit from the `serialize` method in the
        `openaccess_epub.utils.element_methods` module.
        """
        raise NotImplementedError


class PLoS(Publisher):
    """
    """
    def __init__(self):
        super(PLoS, self).__init__()

    def nav_contributors(self, article):
        creator_list = []
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
                new_creator = creator(auth, 'aut', file_as)
                creator_list.append(new_creator)
        return creator_list

    def nav_title(self, article):
        """
        Given an Article class instance, this will return a string representing
        the title of the article. This is done for PloS by serializing the text
        in the Article's
        """
        article_title = article.metadata.front.article_meta.title_group.article_title.node
        return serialize(article_title)

    def package_identifier(self, article):
        """
        Given an Article class instance, this will return the DOI for the article.
        It returns a namedtuple which holds the value and scheme.
        """
        doi = article.get_DOI()
        if doi:
            return identifier(doi, 'DOI')
        else:
            return None

    def package_language(self, article):
        """
        Given an Article class instance, this will return the language in which
        that article was published. Since all PLoS articles are published in
        english, this will return 'en'.
        """
        return 'en'

    def package_title(self, article):
        return self.nav_title(article)

    def package_creator(self, article):
        """
        Given an Article class instance, this is responsible for returning the
        names for creators of the article. For our purposes, it is sufficient to
        list only the authors, returning their name, role=aut, and file-as name.

        This returns a list of Creator(name, role, file_as)
        """
        creator_list = []
        for contrib_group in article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if not contrib.attrs['contrib-type'] == 'author':
                    continue
                if contrib.collab:
                    auth = str(etree.tostring(contrib.collab[0].node, method='text', encoding='utf-8').strip(), encoding='utf-8')
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
                new_creator = creator(auth, 'aut', file_as)
                creator_list.append(new_creator)
        return creator_list

    def package_contributor(self, article):
        """
        Given an Article class instance, this is responsible for returning the
        names for contributors to the article. For our purposes, it is sufficient
        to list only the editors, returning their name, role=edt, and file-as name.

        This returns a list of Contributor(name, role, file_as)
        """
        contributor_list = []
        for contrib_group in article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if not contrib.attrs['contrib-type'] == 'editor':
                    continue
                if contrib.collab:
                    auth = etree.tostring(contrib.collab[0].node, method='text', encoding='utf-8')
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
                new_contributor = contributor(auth, 'edt', file_as)
                contributor_list.append(new_contributor)
        return contributor_list

    def package_publisher(self, article):
        """
        Given an Article class instance, this is responsible for returning a string
        for the name of the publisher. Since the publisher is already known, it
        just returns a string regardless of article content.
        """
        return 'Public Library of Science'

    def package_description(self, article):
        """
        Given an Article class instance, this is responsible for returning an
        article description. For this method I have taken the approach of
        serializing the article's first abstract, if it has one. This results
        in 0 or 1 descriptions per article.
        """
        abstract_text = ''
        abstract = article.metadata.front.article_meta.abstract
        if abstract:
            abstract_text = etree.tostring(abstract[0].node, method='text', encoding='utf-8').strip()
        if abstract_text:
            return str(abstract_text, encoding='utf-8')
        else:
            return ''

    def package_date(self, article):
        """
        Given an Article class instance, this provides the method for extracting
        important dates in the history of the article. These are returned as a list
        of Date(year, month, day, event). This method looks specifically to locate
        the dates when PLoS accepted the article and when it was published online.
        """
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
                if date.attrib['date-type'] == 'accepted':
                    year_el = date.find('year')
                    month_el = date.find('month')
                    day_el = date.find('day')
                    if year_el is not None:
                        year = element_methods.all_text(year_el)
                    else:
                        year = ''
                    if month_el is not None:
                        month = element_methods.all_text(month_el)
                    else:
                        month = ''
                    if day_el is not None:
                        day = element_methods.all_text(day_el)
                    date_list.append(date_tup(year, month, day, 'creation'))

        #Publication is another Dublin Core event value: I use date of epub
        pub_dates = article.metadata.front.article_meta.pub_date
        for pub_date in pub_dates:
            if pub_date.attrs['pub-type'] == 'epub':
                date_list.append(date_tup(pub_date.year.text, pub_date.month.text,
                                          pub_date.day.text, 'publication'))
        return date_list

    def package_subject(self, article):
        """
        Given an Article class instance, this provides a way to extract keyword
        values for use as Dublin Core Subject elements. These are returned as a
        list of strings.
        """
        #Concerned only with kwd elements, not compound-kwd elements
        #Basically just compiling a list of their serialized text
        subject_list = []
        kwd_groups = article.metadata.front.article_meta.kwd_group
        for kwd_group in kwd_groups:
            for kwd in kwd_group.kwd:
                subject_list.append(etree.tostring(kwd.node, method='text', encoding='utf-8'))
        return subject_list


class Frontiers(Publisher):

    def __init__(self):
        super(Frontiers, self).__init__()

    def nav_creators(self, article):
        """
        Frontiers method.

        Given an Article class instance, this is responsible for returning the
        names for creators of the article. For our purposes, it is sufficient to
        list only the authors, returning their name, role=aut, and file-as name.

        This returns a list of Creator(name, role, file_as)
        """
        creator_list = []
        for contrib_group in article.metadata.front.article_meta.contrib_group:
            for contrib in contrib_group.contrib:
                if not contrib.attrs['contrib-type'] == 'author':
                    continue
                if contrib.collab:
                    auth = etree.tostring(contrib.collab[0].node, method='text', encoding='utf-8')
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
                new_creator = creator(auth, 'aut', file_as)
                creator_list.append(new_creator)
        return creator_list

    def nav_title(self, article):
        """
        Frontiers method.

        Given an Article class instance, this will return a string representing
        the title of the article. This is done for PloS by serializing the text
        in the Article's
        """
        article_title = article.metadata.front.article_meta.title_group.article_title.node
        return str(etree.tostring(article_title, method='text', encoding='utf-8'), encoding='utf-8')
