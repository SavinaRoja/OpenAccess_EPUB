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

import openaccess_epub.utils.element_methods as element_methods
from collections import namedtuple
from lxml import etree

identifier = namedtuple('Identifier', 'value, scheme')
creator = namedtuple('Creator', 'name, role, file_as')
contributor = namedtuple('Contributor', 'name, role, file_as')
date_tup = namedtuple('Date', 'year, month, day, event')

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
    article_title = article.metadata.front.article_meta.title_group.article_title.node
    return str(etree.tostring(article_title, method='text', encoding='utf-8'), encoding='utf-8')

def plos_dc_creator(article):
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
                auth = etree.tostring(contrib.collab[0], method='text', encoding='utf-8')
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



def plos_dc_contributor(article):
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
                auth = etree.tostring(contrib.collab[0], method='text', encoding='utf-8')
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
    abstract = article.metadata.front.article_meta.abstract
    if abstract:
        abstract_text = etree.tostring(abstract[0].node, method='text', encoding='utf-8').strip()
    if abstract_text:
        return str(abstract_text, encoding='utf-8')
    else:
        return ''

def plos_dc_date(article):
    """
    Given an Article class instance, this provides the method for extracting
    important dates in the history of the article. These are returned as a list
    of Date(year, month, day, event). This method looks specifically to locate
    the dates when PLoS accepted the article and when it was published online.
    """
    date_list = []
    history = article.metadata.front.article_meta.history
    if history is None:
        return date_list
    #Creation is a Dublin Core event value: I interpret it as the date of acceptance
    #For some reason, the lxml dtd parser fails to recognize the content model
    #history (something to do with expanded content model? I am not sure yet)
    #So for now, this will illustrate a work-around using lxml search
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

def plos_dc_subject(article):
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
        for kwd in kew_group:
            subject_list.append(etree.tostring(kwd.node, method='text', encoding='utf-8'))
    return subject_list



