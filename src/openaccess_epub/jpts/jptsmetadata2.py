# -*- coding: utf-8 -*-
"""
Most, if not all, Open Access journals appear to utilize the Journal Publishing
Tag Set as their archival and interchange data format for their articles.

This module provides classes for extracting the metadata contained within the
JPTS documents and representing them as python elements and data structures.

By way of providing support to multiple versions of the JPTS DTDs (specifically
2.0, 2.1, 2.2, 2.3, and 3.0), the JPTSMetadata class presented within this
module will maintain a so-called "union of metadata sets". As a result of this
feature, certain metadata values or value components may exist in the class
that are not utilized by all DTD versions. It is up to the developer to be
aware of the appropriate values to look up according to the DTD version and the
publisher's usage.
"""

from collections import namedtuple
import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
import openaccess_epub.jpts.jptscontrib as jptscontrib
import logging



log = logging.getLogger('openaccess_epub.jpts.jptsmetadata')


class JPTSInputError(Exception):
    pass


class JPTSMetadata(object):
    """
    This class represents the metadata contained in a document published in
    accordance to the Journal Publish Tag Set in versions 2.0-3.0.

    It will present a union of the metadata sets from these versions, thus
    the developer should be aware of the DTD version for their documents
    and the publisher's usage conventions to later know which values to pull.
    """
    def __init__(self, document, dtd_version=None):
        if dtd_version is None:
            self.detect_dtd_version()
        else:
            self.dtd_version = float(dtd_version)  # A string for DTD version
        self.document = document  # The minidom document element for article
        self.get_top_level_elements()
        self.get_front_child_elements()
        self.parse_metadata()

    def get_top_level_elements(self):
        """
        The various DTD versions define top level elements that occur under the
        document element, <article>.
        """
        #If any of the elements are not found, their value will be None
        #The <front> element is required, and singular
        self.front = self.document.getElementsByTagName('front')[0]
        #The <body> element is 0 or 1; it does not contain metadata
        self.body = element_methods.getOptionalChild('body', self.document)
        #The <back> element is 0 or 1
        self.back = element_methods.getOptionalChild('back', self.document)
        #The <floats-wrap> element is 0 or 1; relevant only to version 2.3
        self.floats_wrap = element_methods.getOptionalChild('floats-wrap', self.document)
        if self.floats_wrap and self.dtd_version != 2.3:
            raise JPTSInputError('floats-wrap valid only in DTD v.2.3')
        #The <floats-group> element is 0 or 1; relevant only to version 3.0
        self.floats_group = element_methods.getOptionaChild('floats-group', self.document)
        if self.floats_group and self.dtd_version != 3.0:
            raise JPTSInputError('floats-group valid only in DTD v.3.0')
        #The <sub-article> and <response> elements are defined in all supported
        #versions in the following manner: 0 or more, mutually exclusive
        self.sub_article = self.document.getElementsByTagName('sub-article')
        if self.sub_article:
            self.response = None
        else:
            self.sub_article = None
            self.response = self.document.getElementsByTagName('response')
            if not self.response:
                self.response = None
        if self.sub_article and self.response:
            raise JPTSInputError('response and sub-article are mutually exclusive')

    def get_front_child_elements(self):
        """
        The various DTD versions all maintain the same definition of the
        elements that may be found directly beneath the <front> element.
        """
        #The <journal-meta> element is required
        self.journal_meta = self.front.getElementsByTagName('journal-meta')[0]
        #The <article-meta> element is required
        self.article_meta = self.front.getElementsByTagName('article-meta')[0]
        #The <notes> element is 0 or 1; if not found, self.notes will be None
        self.notes = element_methods.getOptionalChild('notes', self.front)

    def parse_metadata(self):
        """
        Parses the metadata features present in all versions of the DTD. As
        a general rule, if a certain metadata element is not used in the
        specified version of the DTD, then the value of that element will be
        None.
        """
        ### front ###
        ###   journal-meta ###
        #journal_id is a list of namedtuples : [journal_id(value, type)]
        self.journal_id = self.extract_journal_id()
        #journal_title is a list of namedtuples : [journal_title(value, content_type)]
        self.journal_title = self.extract_journal_title()
        self.journal_title_group = self.extract_journal_title_group()
        ###   article-meta ###

    def extract_journal_id(self):
        """
        <journal-id> is a required, one or more, sub-element of <journal-meta>.
        It can only contain text, numbers, or special characters. It has a
        single potential attribute, 'journal-id-type'.
        """
        jrn_id_tuple= namedtuple('journal_id', 'value, type')
        journal_ids = []
        for journal_id in self.journal_meta.getElementsByTagName('journal-id'):
            text = element_methods.node_text(journal_id)
            type = journal_id.getAttribute('journal-id-type')
            journal_ids.append(jrn_id_tuple(text, type))
        if not journal_ids:
            raise JPTSInputError('Missing mandatory journal-id')
        return journal_ids

    def extract_journal_title(self):
        """
        <journal-title> is defined in DTD versions 2.0-2.3 as 0 or more under
        the <journal-meta> element. In version 2.3, it has an attribute 
        'content-type'. This method will return a list of namedtuples
        [journal_title(value, content_type)] except in the case of v.3.0 where
        it will return None.
        """
        if self.dtd_version == 3.0:  # Not defined in 3.0
            return None
        jrn_title_tuple = namedtuple('journal_title', 'value, content_type')
        journal_titles = []
        for journal_title in self.journal_meta.getElementsByTagName('journal-title'):
            text = element_methods.node_text(journal_title)
            if self.dtd_version != 2.3:
                type = None 
            else:
                type = journal_title.getAttribute('content-type')
            journal_titles.append(jrn_title_tuple(text, type))

    def extract_journal_title_group(self):
        """
        <journal-title-group> is defined only in DTD v.3.0. as 0 or more under
        the <journal-meta> element. It will return a list of named tuples,
        described in further detail below.

        <journal-title-group> is a much more complex title structure, but it
        affords significantly improved function. Beneath this element, 0 or
        more of each of the following elements may occur: <journal-title>,
        <journal-subtitle>, <trans-title-group>, and <abbrev-journal-title>.
        As such, this will return a list of nested namedtuples like so:
          [journal_title_group(
                               [journal_title(value, content_type, xml_lang)],
                               [journal_subtitle(value, content_type, xml_lang)],
                               [trans_title_group(id, content_type, xml_lang],
                                                  trans_title = minidom.element,
                                                  trans_subtitle = [minidom.element]),
                               [abbrev_journal_title(value, abbrev_type, xml_lang)]]
        """
        if self.dtd_version != 3.0:
            return None
        jrn_title_group_tuple = namedtuple('journal_title_group',
                                           'journal_title, journal_subtitle, trans_title_group, abbrev_journal_title')
        jrn_title_tuple = namedtuple('journal_title', 'value, content_type, xml_lang')
        jrn_subtitle_tuple = namedtuple('journal_subtitle', 'value, content_type, xml_lang')
        
        abbrev_jrn_title_tuple = namedtuple('abbrev_journal_title', 'value, abbrev_type, xml_lang')
        journal_title_groups = []
        for jrn_title_grp in self.journal_meta.getElementsByTagName('journal-title-group'):
            jrn_titles = []
            for jrn_title in jrn_title_grp.getElementsByTagName('journal-title'):
                data_tuple = jrn_title_tuple(element_methods.node_text(jrn_title),
                                             jrn_title.getAttribute('content-type'),
                                             jrn_title.getAttribute('xml:lang'))
                jrn_titles.append(data_tuple)
            jrn_subtitles = []
            for jrn_subtitle in jrn_title_grp.getElementsByTagName('journal-subtitle'):
                data_tuple = jrn_subtitle_tuple(element_methods.node_text(jrn_subtitle),
                                                jrn_subtitle.getAttribute('content-type'),
                                                jrn_subtitle.getAttribute('xml:lang'))
                jrn_subtitles.append(data_tuple)
            trans_title_groups = []
            for trans_title_grp in jrn_title_grp.getElementsByTagName('trans-title-group'):
                data_tuple = None
                trans_title_groups.append(data_tuple)
            abbrev_jrn_titles = []
            for abbrev_jrn_title in jrn_title_grp.getElementsByTagName('abbrev-journal-title'):
                data_tuple = abbrev_jrn_title_tuple(element_methods.node_text(abbrev_jrn_title),
                                                    abbrev_jrn_title.getAttribute('abbrev-type'),
                                                    abbrev_jrn_title.getAttribute('xml:lang'))
                abbrev_jrn_titles.append(data_tuple)
            journal_title_groups.append(jrn_title_group_tuple(jrn_titles, jrn_subtitles,
                                                              trans_title_groups, abbrev_jrn_titles))
        return journal_title_groups

    def pack_node_to_namedtuple(self, node, get_child=None,
                                get_childlist=None, get_attrs=None, get_text=False):
        """
        This class function provides a consistent tool for doing the frequent
        job of extracting different attributes of a node and placing them in
        a well-defined namedtuple.

        The function will define the namedtuple's name according to the tagName
        of the node it receives, and the namedtuple's attribute names will be
        defined according to their kind.*

        If get_child is supplied a list of tagNames, then it will seek to find
        the first, or only, instance of that tagName amongst the node's
        childNodes. For example, get_child=['title'] would result in a
        namedtuple attribute name 'title', whose value is the DOM element.
        Similarly, if get_childlist is supplied a list of tagNames, it will
        behave in the same way, except it will return all instances as a list.
        
        If get_attrs is supplied a list of strings, then it will seek to get
        each of these attributes.

        *Note that all non-alphanumeric characters will be replaced by
        by underscores.
        """
        if get_child is None:
            get_child = []
        if get_childlist is None:
            get_childlist = []
        if get_attrs is None:
            get_attrs = []

        field_names = []
        field_vals = []

        if get_text:
            field_names.append('value')
            field_vals.append(element_methods.node_text(node))
        for child_string in get_child:
            field_names.append(child_string)
            field_vals.append(element_methods.get_optional_child(child_string))
        for child_string in get_childlist:
            field_names.append(child_string)
            field_vals.append(element_methods.get_children_by_tag_name(child_string))
        for attr_string in get_attrs:
            field_names.append(attr_string)
            field_vals.append(node.getAttribute(attr_string))

        def coerce_string(input):
            for char in input:
                if char.lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_':
                    input = input.replace(char, '_')
            return input

        data_tuple = namedtuple(node.tagName, ', '.join([coerce_string(i) for i in field_names]))
        return data_tuple(*field_vals)


    def detect_dtd_version(self):
        dtds = {'-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN': 2.0,
                '-//NLM//DTD Journal Publishing DTD v2.1 20050630//EN': 2.1,
                '-//NLM//DTD Journal Publishing DTD v2.2 20060430//EN': 2.2,
                '-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN': 2.3,
                '-//NLM//DTD Journal Publishing DTD v3.0 20080202//EN': 3.0}
        try:
            self.dtd_version = dtds[self.document.doctype.publicId]
        except KeyError as err:
            print('Received a document of an unsupported DTD.')
            raise err
