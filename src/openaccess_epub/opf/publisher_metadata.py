# -*- coding: utf-8 -*-
"""
The methods in this file follow the prescription below for pulling metadata
from the JPTS Metadata class. This class is instantiated for each article and
is accessed by Article attribute article.metadata. Each method should expect to
receive an instance of the Article class.

_dc_identifer :   returns Identifier or None - Identifier|None
_dc_language :    returns string (should be RFC 1766 value) - ''
_dc_title :       returns string - ''
_dc_creator :     returns list of Creator - [Creator]
_dc_contributor : returns list of Contributor - [Contributor]
_dc_publisher :   returns string - ''
_dc_description : returns string - ''
_dc_date :        returns list of Date - [Date]
_dc_subject :     returns list of string - ['']
"""

from collections import namedtuple
import openaccess_epub.utils as utils

identifier = namedtuple('Identifier', 'value, scheme')
creator = namedtuple('Creator', 'name, role, file_as')
contributor = namedtuple('Contributor', 'name, role, file_as')
date = namedtuple('Date', 'year, month, day, event')

#### Public Library of Science - PLoS ###
def plos_dc_identifier(article):
    """
    Given an Article class instance, this will return the DOI for the article.
    It returns a namedtuple which holds the value and scheme.
    """
    doi = article.get_DOI()
    if doi:
        return identifier(doi, 'DOI')
    else:
        return None

def plos_dc_language(article):
    """
    Given an Article class instance, this will return the language in which
    that article was published. Since all PLoS articles are published in
    english, this will return 'en'.
    """
    return 'en'

def plos_dc_title(article):
    """
    Given an Article class instance, this will return a string representing
    the title of the article. This is done for PloS by serializing the text
    in the Article's
    """
    title_node = article.metadata.title.article_title
    title_string = utils.serialize_text(title_node)
    return title_string

def plos_dc_creator(article):
    """
    Given an Article class instance, this is responsible for returning the
    names for creators of the article. For our purposes, it is sufficient to
    list only the authors, returning their name, role=aut, and file-as name.

    This returns a list of Creator(name, role, file_as)
    """
    creator_list = []
    for contrib in article.metadata.contrib:
        if contrib.attrs['contrib-type'] == 'author':
            if contrib.collab:
                auth = utils.serializeText(contrib.collab[0])
                file_as = auth
            elif contrib.anonymous:
                auth = 'Anonymous'
                file_as = auth
            else:
                name = contrib.getName()[0]  # Work with only first name listed
                surname = name.surname
                given = name.given
                try:
                    gi = given[0]
                except (IndexError, TypeError):
                    auth = surname
                    file_as = surname
                else:
                    auth = ' '.join([given, surname])
                    file_as = ', '.join([surname, gi])
            new_creator = creator(auth, 'aut', file_as)
            creator_list.append(new_creator)
    return creator_list

def plos_dc_contributor(article):
    """
    Given an Article class instance, this is responsible for returning the
    names for contributors to the article. For our purposes, it is sufficient
    to list only the editors, returning their name, role=edt, and file-as name.

    This returns a list of Contributor(name, role, file_as)
    """
    contributor_list = []
    for contrib in article.metadata.contrib:
        if contrib.attrs['contrib-type'] == 'editor':
            if contrib.collab:
                editor_name = utils.serializeText(contrib.collab[0])
                file_as = editor_name
            else:
                name = contrib.getName()[0]
                try:
                    given_initial = name.given[0]
                except TypeError:
                    editor_name = name.surname
                    file_as = name.surname
                else:
                    editor_name = name.given + ' ' + name.surname
                    file_as = name.surname + ', ' + given_initial
            new_contributor = contributor(editor_name, 'edt', file_as)
            contributor_list.append(new_contributor)
    return contributor_list

def plos_dc_publisher(article):
    """
    Given an Article class instance, this is responsible for returning a string
    for the name of the publisher. Since the publisher is already known, it
    just returns a string regardless of article content.
    """
    return 'Public Library of Science'

def plos_dc_description(article):
    """
    Given an Article class instance, this is responsible for returning an
    article description. For this method I have taken the approach of
    serializing the article's first abstract, if it has one. This results
    in 0 or 1 descriptions per article.
    """
    abstract_text = ''
    if article.metadata.abstract:
        abstract_text = utils.serialize_text(article.metadata.abstract[0].node)
    return abstract_text

def plos_dc_date(article):
    """
    Given an Article class instance, this provides the method for extracting
    important dates in the history of the article. These are returned as a list
    of Date(year, month, day, event). This method looks specifically to locate
    the dates when PLoS accepted the article and when it was published online.
    """
    date_list = []
    #Creation is a Dublin Core event value: I interpret it as the accepted date
    creation_date = article.metadata.history['accepted']
    if creation_date:
        date_list.append(date(creation_date.year,
                              creation_date.month,
                              creation_date.day,
                              'creation'))
    #Publication is another Dublin Core event value: epub
    try:
        pub_date = article.metadata.pub_date['epub']
    except KeyError:
        pass
    else:
        date_list.append(date(pub_date.year,
                              pub_date.month,
                              pub_date.day,
                              'publication'))
    return date_list

def plos_dc_subject(article):
    """
    Given an Article class instance, this provides a way to extract keyword
    values for use as Dublin Core Subject elements. These are returned as a
    list of strings.
    """
    subject_list = []
    for kwd in article.metadata.all_kwds:
        kwd_text = utils.serialize_text(kwd.node)
        subject_list.append(kwd_text)
    return subject_list



