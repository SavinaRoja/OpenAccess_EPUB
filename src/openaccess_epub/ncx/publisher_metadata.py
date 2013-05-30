# -*- coding: utf-8 -*-
"""
The methods in this file follow the prescription below for pulling metadata
from the JPTS Metadata class for use by the NCX. The NCX requires only the
authors of the article and the title. Each method should expect an instance of
the Article class, and return a list of Creator namedtuples.

_creator : returns list of Creator - [Creator]
_title :   returns string - ''
"""

from collections import namedtuple
import openaccess_epub.utils as utils

creator = namedtuple('Creator', 'name, role, file_as')

#### Public Library of Science - PLoS ###
def plos_creator(article):
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

def plos_title(article):
    """
    Given an Article class instance, this will return a string representing
    the title of the article. This is done for PloS by serializing the text
    in the Article's
    """
    title_node = article.metadata.title.article_title
    title_string = utils.serialize_text(title_node)
    return title_string