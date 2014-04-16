# -*- coding: utf-8 -*-

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


class Frontiers(Publisher):

    def __init__(self):
        super(Frontiers, self).__init__()
        self.epub2_support = False
        self.epub3_support = False

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

pub_class = Frontiers