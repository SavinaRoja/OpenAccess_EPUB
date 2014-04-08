# -*- coding: utf-8 -*-

"""
openaccess_epub.publisher defines abstract publisher representation and content
conversion
"""

#Standard Library modules
import os
from collections import namedtuple
import logging
import sys
try:
    from importlib.abc import SourceLoader
except ImportError:
    from importlib.abc import PyLoader as SourceLoader
from importlib import import_module

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub.utils.element_methods import all_text, serialize
from openaccess_epub.utils import publisher_plugin_location

log = logging.getLogger('openaccess_epub.publisher')

contributor_tuple = namedtuple('Contributor', 'name, role, file_as')
date_tuple = namedtuple('Date', 'year, month, day, event')
identifier_tuple = namedtuple('Identifier', 'value, scheme')


### Section Start - Dynamic Extension with publisher_plugins folder ############
################################################################################
#The code in this section is devoting to creating easy publisher-wise extension
#for rapid testing and development without modifying installed source
plugin_dir = publisher_plugin_location()
doi_map_file = os.path.join(plugin_dir, 'doi_map')

doi_map = {'10.1371': 'plos',
           '10.3389': 'frontiers'}

#By inserting at the beginning, the plugin directory will override the source
#modules if they exist
__path__.insert(0, publisher_plugin_location())

if not os.path.isfile(doi_map_file):
    os.makedirs(os.path.dirname(doi_map_file))
    with open(doi_map_file, 'a'):
        os.utime(doi_map_file, None)

with open(doi_map_file, 'r') as mapping:
    for line in mapping:
        key, val = line.split(':')
        doi_map[key.strip()] = val.strip()


class PublisherFinder(object):
    prefix = 'openaccess_epub.publisher'

    def __init__(self, path_entry):
        if path_entry not in __path__:
            raise ImportError
        else:
            self.path_entry = path_entry
            return None

    def find_module(self, fullname, path=None):
        path = path or self.path_entry
        name = fullname.split('.')[-1]
        for fname in [os.path.join(i, name + '.py') for i in __path__]:
            if os.path.isfile(fname):
                return PublisherLoader(path)
        return None


class PublisherLoader(SourceLoader):

    def __init__(self, path_entry):
        self.path_entry = path_entry
        return None

    #This is poorly documented, the argument to get_data is implicitly supplied
    #by a call to get_filename
    def get_data(self, filepath):
        with open(filepath, 'r') as source:
            return bytes(source.read(), 'utf-8')

    def get_filename(self, path):
        name = path.split('.')[-1]
        for fname in [os.path.join(i, name + '.py') for i in __path__]:
            if os.path.isfile(fname):
                return fname
        return None

sys.path_hooks.append(PublisherFinder)


def import_by_doi(doi):
    return import_module('.'.join([__name__, doi_map[doi]]))
### Section End - Dynamic Extension with publisher_plugins folder ##############
################################################################################

def func_registrar():
    func_list = []

    def register(func):
        func_list.append(func)
        return func
    register.all = func_list
    return register


class Publisher(object):
    """
    Meta class for publishers, sub-class per publisher to add support
    """

    #Maker methods are for generating content
    maker2 = func_registrar()  # EPUB2 methods
    maker3 = func_registrar()  # EPUB3 methods

    #Special methods are for elegant pre-processing, prior to ignorant recursive
    #iteration through the document tree to convert elements
    special2 = func_registrar()  # EPUB2 methods
    special3 = func_registrar()  # EPUB3 methods

    def __init__(self):
        """
        The initialization of the Publisher class.
        """
        self.epub2_support = False
        self.epub3_support = False
        self.epub2_maker_methods = self.maker2.all
        self.epub3_maker_methods = self.maker3.all
        self.epub2_special_methods = self.special2.all
        self.epub3_special_methods = self.special3.all

    def render_content(self, epub_version):
        if int(epub_version) == 2:
            if not self.epub2_support:
                log.error('EPUB2 not supported by this publisher')
                raise NotImplementedError('EPUB2 is not supported')
            else:
                for func in self.epub2_maker_methods:
                    self.__getattribute__(func.__name__)()
                for func in self.epub2_special_methods:
                    self.__getattribute__(func.__name__)()
        elif int(epub_version) == 3:
            if not self.epub3_support:
                log.error('EPUB3 not supported by this publisher')
                raise NotImplementedError('EPUB3 is not supported')
            else:
                for func in self.epub3_maker_methods:
                    self.__getattribute__(func.__name__)()
                for func in self.epub3_special_methods:
                    self.__getattribute__(func.__name__)()
        else:
            log.error('Improper EPUB version specified')
            raise ValueError('epub_version should be 2 or 3')

    def nav_contributors(self):
        """
        Returns a list of contributors to the article.

        This is a metadata method that is only required to be defined for
        EPUB2 creation, though the `package_contributors` counterpart should
        always be present. This method returns a list of special namedtuples
        with the following specification: Contributor(name, role, file_as).
        The 'name' should be a string representing a standard reading form of
        the contributor's name. The 'role' will indicate one of the following:
        'author', 'editor', and 'reviewer'. The 'file_as' will be a string
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
            A list of contributors, [Contributor(name, role, file_as)].

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
        str
            The `title` of the article being parsed for metadata.

        Notes
        -----
        This method is likely to benefit from the `serialize` method in the
        `openaccess_epub.utils.element_methods` module.
        """
        raise NotImplementedError

    def package_identifier(self, article):
        """
        Returns an identifier for the article.

        This is a required metadata method used for representing a unique
        identifier for the article. Typically this will simply be the article's
        DOI. The namedtuple which this method returns is of the form
        Identifier(value, scheme).

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        Identifier namedtuple
            A single Identifier(value, scheme).
        """
        raise NotImplementedError

    def package_language(self, article):
        """
        Returns a list of language tags indicating languages used in the
        article.

        This is a required metadata method used to indicate the languages in
        which the content of the article is written. This method returns a list
        of string language codes (which must conform to
        http://tools.ietf.org/html/rfc5646).

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        list of str
            A list of strings conforming to language codes.
        """
        raise NotImplementedError

    def package_title(self, article):
        """
        Returns a string for the title of the article.

        This is a required metadata method used for representing the article's
        title in the Package Document of the EPUB. It simply returns a string
        of the title's text. It may differ from `nav_title` but it is also
        likely that these methods may be the same, in which case one may use a
        strategy to ensure they return the same results.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        str
            The `title` of the article being parsed for metadata.

        Notes
        -----
        This method is likely to benefit from the `serialize` method in the
        `openaccess_epub.utils.element_methods` module.
        """
        raise NotImplementedError

    #TODO: Implement alternate-language scripts for contributors
    def package_contributors(self, article):
        """
        Returns a list of contributors to the article.

        This method returns a list of special namedtuples representing
        contributors to the article. These follow the follow specification:
        Contributor(name, role, file_as). The 'name' should be a string
        representing a standard reading form of the contributor's name. The
        'role' should be a MARC relator value (see References).
        The 'file_as' will be a string representing a name as it
        would be catalogued. This method may differ from `nav_contributors`
        if one desires, but they generally overlap.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        list of Contributor namedtuples
            A list of contributors, [Contributor(name, role, file_as)].

        Notes
        -----
        Appropriate entries for authors and editors will be created in the
        Packaging Document using the data returned by this method.

        References
        ----------
        http://www.loc.gov/marc/relators/relaterm.html
        http://www.loc.gov/marc/relators/relacode.html
        """
        raise NotImplementedError

    def package_subject(self, article):
        """
        Returns a list of strings representing keyword subjects relevant to the
        article's content.

        This is an optional metadata method representing keyword subjects
        covered in the article's content. Each string returned in the list will
        be added to the Package Document metadata as a keyword.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        list of str
            List of keyword strings representing content subjects.
        """
        return []

    def package_publisher(self, article):
        """
        Returns the full name of the publsher as it should be written in the
        Package Document metadata.

        This is an optional metadata method for entering the publisher's name
        in the Package Document metadata. This is super simple, just return a
        string for your publisher name.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        str
            Name of the publisher.
        """
        return ''

    def package_description(self, article):
        """
        Returns a string description of the article. This may be the serialized
        text of the abstract.

        This is an optional metadata method for entering a description of the
        article in the Package Document metadata. In many cases, the description
        may be best provided by the article's abstract if it has one. This
        returns a string of plain text, though the abstract may commonly include
        nested XML elements; serializing the abstract should be employed.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        str or None
            Description of the article. None if no description available.
        """
        return None

    def package_date(self, article):
        """
        Returns a list of important dates for the article.

        This is an optional metadata method which may be used to make entries
        for important dates in the Package Document metadata. This method
        returns a list of special Date namedtuples which are of the form:
        Date(year, month, day, event). The event value should be one of
        'accepted', 'copyrighted', 'submitted', None if not used.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        list of Date namedtuples
            A list of dates, [Date(year, month, day, event)].
        """
        return []

    def package_rights(self, article):
        """
        Returns a string representing a copyright statement for the article.

        This is a requied metadata method which will be used to provide an
        appropriate statement of rights in the Package Document. This method
        should return a string.

        Parameters
        ----------
        article : openaccess_epub.article.Article instance
            The `article` which is being parsed for metadata.

        Returns
        -------
        str
            A string for the copyright statement of the article.

        Notes
        -----
        Elegantly handling rights from multiple works within the Package
        Document may be a challenge but very important. Constructive feedback is
        highly welcome at all times to attempt to follow best practices. I will
        review aspects of this challenge, as well as summarize how the Package
        Document handles it.

        Most OA articles are published under a variant of the Creative Commons
        license, and different versions of this license retain differ in terms
        or rights and restrictions. Due to the fact that articles may be
        published under different licenses, care should be taken to ensure that
        clear notice is given to the licensing of individual articles and that
        incompatible licenses are not mixed.

        Creating an EPUB of an article (or compiling them in a collection) is
        considered the creation of a derivative work; the EPUB should not be
        considered a verbatim copy of the work. Licenses which do not allow
        derivative works are not compatible with OpenAccess_EPUB. Likewise, the
        use of OpenAccess_EPUB to create content for commercial purposes is
        not compatible with licenses that prohibit commercial use. It is not the
        responsibility of OpenAccess_EPUB (an open source, freely available and
        modifiable software) to enforce conformance to licensing rules.

        If all articles in a collection are published according to the same
        license, a rights entry will be made in the Package Document displaying
        that license along with a note that it pertains to all articles. If
        there are multiple licenses in the collection, a rights entry will be
        created which details each individual license, along with the distinct
        articles to which they pertain.
        """
        return NotImplementedError


class PLoS(Publisher):
    """
    """
    def __init__(self):
        super(PLoS, self).__init__()

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
