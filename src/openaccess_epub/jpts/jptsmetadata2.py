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
        self.document = document  # The minidom document element for article
        if dtd_version is None:
            self.detect_dtd_version()
        else:
            self.dtd_version = float(dtd_version)  # A float for DTD version
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
        self.body = element_methods.get_optional_child('body', self.document)
        #The <back> element is 0 or 1
        self.back = element_methods.get_optional_child('back', self.document)
        #The <floats-wrap> element is 0 or 1; relevant only to version 2.3
        self.floats_wrap = element_methods.get_optional_child('floats-wrap', self.document)
        if self.floats_wrap and self.dtd_version != 2.3:
            raise JPTSInputError('floats-wrap valid only in DTD v.2.3')
        #The <floats-group> element is 0 or 1; relevant only to version 3.0
        self.floats_group = element_methods.get_optional_child('floats-group', self.document)
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
        self.notes = element_methods.get_optional_child('notes', self.front)

    def parse_metadata(self):
        """
        Parses the metadata features present in all versions of the DTD.

        As a general rule, if a metadata element is not utilized at all in a
        specific version of the DTD then that element's value will be None.
        There may be other cases where elements differ only in attributes or
        subelements.
        """
        ### front ###
        ###   journal-meta ###
        #journal_id is a list of namedtuples : [journal_id(value, type)]
        self.journal_id = self.extract_journal_id()
        #journal_title is a list of namedtuples : [journal_title(value, content_type)]
        self.journal_title = self.extract_journal_title()
        #journal_title_group is only in 3.0 : see extract_journal_title_group
        self.journal_title_group = self.extract_journal_title_group()
        #journal_subtitle only in 2.1-2.3 :  [journal_title(value, content_type)]
        self.journal_subtitle = self.extract_journal_subtitle()
        #trans_title only in 2.3: []
        self.trans_title = self.extract_trans_title()
        #trans_subtitle only in 2.3: []
        self.trans_subtitle = self.extract_trans_subtitle()
        #abbrev_journal_title only in v2.0-2.3 : [abbrev_journal_title(value, abbrev_type)]
        self.abbrev_journal_title = self.extract_abbrev_journal_title()
        #issn is 1 or more in all versions : [issn(value, pub_type)]
        self.issn = self.extract_issn()
        #isbn is 0 or more, only in v.3.0 : [isbn(value, content_type)]
        self.isbn = self.extract_isbn()
        #publisher is 0 or 1 in all versions; None or publisher(name, content_type, loc)
        self.publisher = self.extract_publisher()
        #notes is 0 or 1 in all versions : notes(node, id, notes_type, specific_use)
        self.notes = self.extract_notes
        ###   article-meta ###
        #article_id is 0 or more, in all versions
        self.article_id = self.extract_article_id()
        #article_categories is 0 or 1 in all versions, recursive underneath.
        self.article_categories = self.extract_article_categories()
        #title_group is 1 in all versions, see method for model
        self.title_group = self.extract_title_group()
        #contrib_group is 0+, very complex underlying model
        self.contrib_group = self.extract_contrib_group()

    def extract_journal_id(self):
        """
        <journal-id> is a required, one or more, sub-element of <journal-meta>.
        It can only contain text, numbers, or special characters. It has a
        single potential attribute, 'journal-id-type'.
        """
        jrn_id_tuple= namedtuple('journal_id', 'value, type')
        journal_ids = []
        for journal_id in self.journal_meta.getElementsByTagName('journal-id'):
            journal_ids.append(self.pack_node(journal_id,
                                              get_attrs=['journal-id-type'],
                                              get_text=True))
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
                jrn_titles.append(self.pack_node(jrn_title,
                                                 get_attrs=['content-type', 'xml:lang'],
                                                 get_text=True))
            jrn_subtitles = []
            for jrn_subtitle in jrn_title_grp.getElementsByTagName('journal-subtitle'):
                jrn_subtitles.append(self.pack_node(jrn_subtitle,
                                                    get_attrs=['content-type', 'xml:lang'],
                                                    get_text=True))
            trans_title_groups = []
            for trans_title_grp in jrn_title_grp.getElementsByTagName('trans-title-group'):
                trans_title_groups.append(self.pack_node(trans_title_group,
                                                         get_child=['trans-title'],
                                                         get_childlist=['trans-subtitle'],
                                                         get_attrs=['id', 'content-type', 'xml:lan']))
            abbrev_jrn_titles = []
            for abbrev_jrn_title in jrn_title_grp.getElementsByTagName('abbrev-journal-title'):
                abbrev_jrn_titles.append(self.pack_node(abbrev_jrn_title),
                                         get_attrs=['abbrev-type', 'xml:lang'],
                                         get_text=True)
            journal_title_groups.append(jrn_title_group_tuple(jrn_titles, jrn_subtitles,
                                                              trans_title_groups, abbrev_jrn_titles))
        return journal_title_groups

    def extract_journal_subtitle(self):
        """
        <journal-subtitle> is defined under <journal-meta> in DTD v.2.1-2.3 as
        0 or more. Only in v.2.3 does it have the attribute 'content-type'.

        This will return a list of namedtuples (in v.2.1-2.3), or None
        [journal_subtitle(value, content_type)]
        """
        if self.dtd_version not in [2.1, 2.2, 2.3]:
            return None
        jrn_subtitle_tuple = namedtuple('journal_subtitle', 'value, content_type')
        journal_subtitles = []
        for jrn_subtitle in self.journal_meta.getElementsByTagName('journal-subtitle'):
            if self.dtd_version == 2.3:
                type = jrn_subtitle.getAttribute
            else:
                type = None
            text = element_methods.node_text(jrn_subtitle)
            journal_subtitles.append(jrn_subtitle_tuple(text, type))
        return journal_subtitles

    def extract_trans_title(self):
        """
        <trans-title> is defined under <journal-meta> in DTD v.2.3 as 0 or
        more.

        This will return a list of namedtuples (in v.2.3) or None
        [trans_title(value, content_type, id, xml_lang)]
        """
        if self.dtd_version != 2.3:
            return None
        trans_titles = []
        for trans_title in self.journal_meta.getElementsByTagName('trans-title'):
            trans_titles.appen(self.pack_node(trans_title,
                                              get_attrs=['content-type', 'id', 'xml:lang'],
                                              get_text=True))
        return trans_titles

    def extract_trans_subtitle(self):
        """
        <trans-subtitle> is defined under <journal-meta> in DTD v.2.3 as 0 or
        more.

        This will return a list of namedtuples (in v.2.3) or None
        [trans_subtitle(value, content_type, id, xml_lang)]
        """
        if self.dtd_version != 2.3:
            return None
        trans_subtitles = []
        for trans_subtitle in self.journal_meta.getElementsByTagName('trans-title'):
            trans_subtitles.appen(self.pack_node(trans_subtitle,
                                                 get_attrs=['content-type', 'id', 'xml:lang'],
                                                 get_self=True))
        return trans_subtitles

    def extract_abbrev_journal_title(self):
        """
        <abbrev-journal-subtitle> is defined under <journal-meta> in DTD
        v.2.0-2.3 as 0 or more. It has the one attribute, 'abbrev-type'.

        This will return a list of namedtuples (or None in v.3.0).
        [abbrev_journal_title(value, abbrev_type)]
        """
        if self.dtd_version == 3.0:
            return None
        abbrev_journal_titles = []
        for abbrev_jrn_title in self.journal_meta.getElementsByTagName('abbrev-journal-title'):
            abbrev_journal_titles.append(self.pack_node(abbrev_jrn_title,
                                                        get_attrs=['abbrev-type']))
        return abbrev_journal_titles

    def extract_issn(self):
        """
        <issn> is defined as 1 or more under <journal-meta> in all versions of
        the JPTS DTD. It has one attribute, 'pub-type'.

        This will return a list of namedtuples for the issn elements.
        [issn(value, pub_type)]
        """
        issns = []
        for issn in self.journal_meta.getElementsByTagName('issn'):
            issns.append(self.pack_node(issn, get_attrs=['pub-type']))
        if not issns:
            raise JPTSInputError('Missing mandatory ISSN element')
        return issns

    def extract_isbn(self):
        """
        <isbn> is defined as 0 or more under <journal-meta> in DTD v.3.0. It
        has one attribute, 'content-type'.

        This will return a list of namedtuples for the isbn elements.
        [isbn(value, content_type)]
        """
        isbns = []
        for isbn in self.journal_meta.getElementsByTagName('isbn'):
            isbns.append(self.pack_node(isbn, get_attrs=['content-type']))
        return isbns

    def extract_publisher(self):
        """
        <publisher> is defined under <journal-meta> for all DTD versions, but
        with some variations. It is 0 or 1, so it will return a single element.

        For DTD v.2.3-3.0, the <publisher> element has an attribute,
        'content-type', which is not in the other versions.

        For all DTD versions, the <publisher-name> sub-element is text only
        and has no attributes, so the text value of it is directly accessible
        in the namedtuple of publisher.

        For DTD v.2.0-2.1, the <publisher-loc> is text only and has no
        attributes. For the other versions, the<publisher-loc> sub element may
        contain additional elements (email, ext-link, and uri). In the former
        case, text is returned; in the latter, the node is returned. In both
        cases, if the element is not found, its value will be None.
        """
        publisher_tuple = namedtuple('publisher', 'name, content_type, loc')
        publisher = element_methods.get_optional_child('publisher', self.journal_meta)
        if publisher is None:
            return None
        if self.dtd_version > 2.2:
            content_type = publisher.getAttribute('content-type')
        else:
            content_type = None
        publisher_name = element_methods.get_optional_child('publisher-name', publisher)
        if publisher_name is None:
            raise JPTSInputError('Missing mandatory publisher-name element')
        name = element_methods.node_text(publisher_name)
        publisher_loc = element_methods.get_optional_child('publisher-loc', publisher)
        if self.dtd_version < 2.2 and publisher_loc is not None:
            loc = element_methods.node_text(publisher_loc)
        else:
            loc = None
        return publisher_tuple(name, content_type, loc)

    def extract_notes(self):
        """
        <notes> is defined under <journal-meta> for all DTD versions and is 0
        or 1.

        Because notes has a very complex content model, this will only return
        the node alongside its attributes in a namedtuple.
        """
        notes = element_methods.get_optional_child('notes', self.journal_meta)
        if notes is None:
            return None
        return self.pack_node(notes,
                              get_attrs=['id','notes-type', 'specific-use'],
                              get_self=True)

    def extract_article_id(self):
        """
        <article-id> is defined under <article-meta> for all versions of the
        DTD as 0 or more. All versions provide the same potential attribute,
        'pub-id-type'.
        """
        article_ids = []
        for article_id in self.article_meta.getElementsByTagName('article-d'):
            article_ids.append(self.pack_node(article_id,
                                              get_attrs=['pub-id-type'],
                                              get_text=True))
        return article_ids

    def extract_article_categories(self):
        """
        <article-categories> is defined as 0 or 1 under <article-meta> for all
        versions of the DTD.

        It has no attributes. It may have the following children:
           <series-title> : 0 or more, text and style elements
           <series-text> : 0 or 1, text and style elements
           <subject-group> : 0 or more, contains <subject> and <subject-group>
                             Leads to recursive nesting

        This will return a namedtuple that holds the nodes for <series-title>
        and <series-text>, along with variable-depth structure to hold the
        nested <subject-groups>.
        """

        def get_nested_subject_groups(node):
            subject_group_tuple = namedtuple('subject_group', 'subject, subj_group, type')

            subjects = element_methods.get_children_by_tag_name('subject', node)
            if not subjects:
                raise JPTSInputError('subject-group should have at least one subject')
            subject_groups = []
            for subgroup in element_methods.get_children_by_tag_name('subj-group', node):
                subject_groups.append(get_nested_subject_groups(subgroup))
            type = node.getAttribute('subject-group-type')
            return subject_group_tuple(subjects, subject_groups, type)

        art_cat_tuple = namedtuple('article_categories',
                                   'series_text, series_title, subj_group')
        article_categories = element_methods.get_optional_child('article-categories', self.article_meta)
        if not article_categories:
            return None
        series_text = element_methods.get_optional_child('series-text', article_categories)
        series_titles = element_methods.get_children_by_tag_name('series-title', article_categories)
        subject_groups = []
        for subject_group in element_methods.get_children_by_tag_name('subj-group', article_categories):
            subject_groups.append(get_nested_subject_groups(subject_group))
        return art_cat_tuple(series_text, series_titles, subject_groups)

    def extract_title_group(self):
        """
        <title-group> is defined under <article-meta> for all versions of the
        DTD as a required singular element. There are defined sub-components,
        but there are significant differences between the versions of the DTD.
        These will be discussed below, in relation to version and data type:

            <article-title> : 1, complex data model - DOM Element
            <subtitle>: 0+, complex data model - [DOM Element]
            (in v.2.0, trans-subtitle does not exist)
            (in v.2.1-2.3, they have alternating order for co-relationship)
            |<trans-title>: 0+, See below
            |<trans-subtitle>: 0+, See below
            <trans-title-group>: 0+ (v.3.0) - Defined, with complex children - 
                namedtuple with some DOM Element attributes
            <alt-title>: 0+, complex data model - [Dom Element]
            Footnote Group <fn-group>: 0 or 1, well-defined - namedtuple

        The use of alternating order for co-relating translated titles and sub-
        titles is not a nice thing to do. *shakes fist*. v.2.0 does not employ
        trans-subtitle at all. Because of the co-relation between trans-title
        and trans-subtitle, the trans_subtitle property will be a sub-property
        of trans_title in the case of v.2.1-2.3.

        To make this more clear, to grab the values of <trans-subtitle>, in
        relation to their <trans-title>, one might use the following address:
            subtitle_list = metadata.title_group.trans_title[0].trans_subtitle

        In the case of v.3.0, all of this nonsense is neatly handled in the
        trans_title_group element, and you might use the following to get the
        title and its sub-titles:
            first_trans_title_group = metadata.title_group.trans_title_group[0]
            trans_title = first_trans_title_group.trans_title
            trans_subtitle_list = first_trans_title_group.trans_subtitle
        """
        title_grp_tuple = namedtuple('title_group', 'article_title, subtitle, \
trans_title, trans_title_group, alt_title, fn_group')

        #Get the title group, error if not there
        title_grp = element_methods.get_optional_child('title-group', self.article_meta)
        if title_grp is None:
            raise JPTSInputError('Missing mandatory title-group element in article-meta')

        #Get the article title, error if not there
        article_title_el = element_methods.get_optional_child('article-title', title_grp)
        if article_title_el is None:
            raise JPTSInputError('Missing mandatory article-title element in title-group')
        article_title = self.pack_node(article_title_el,
                                       get_attrs=['id', 'xml:lang', ],
                                       get_self=True)

        #get the subtitles
        subtitles = []
        for subtitle in element_methods.get_children_by_tag_name('subtitle', title_grp):
            subtitles.append(self.pack_node(subtitle,
                                            get_attrs=['xml:lang', 'content-type'],
                                            get_self=True))
        
        #Get the alt titles
        alt_titles = []
        for alt_title in element_methods.get_children_by_tag_name('alt-title', title_grp):
            alt_titles.append(self.pack_node(alt_title,
                                             get_attrs=['alt-title-type'],
                                             get_self=True))

        #Get the footnote group
        fn_group_el = element_methods.get_optional_child('fn-group', title_grp)
        if fn_group_el:
            fn_group = self.pack_node(fn_group_el,
                                      get_child=['label', 'title'],
                                      get_childlist=['fn'],
                                      get_attrs=['content-type', 'id', 'specific-use'])
        else:
            fn_group = None
        #Now the fun part... translated title stuffs
        if self.dtd_version == 2.0:
            trans_title_groups = None
            #get trans-title, list of namedtuple
            trans_title_els = element_methods.get_children_by_tag_name('trans-title', title_grp)
            trans_titles = []
            for trans_title_el in trans_title_els:
                trans_titles.append(self.pack_node(trans_title_el,
                                                   get_attrs=['xml:lang'],
                                                   get_self=True))
        elif self.dtd_version in [2.1, 2.2, 2.3]:
            trans_title_groups = None
            def iter_get_trans_titles(node):
                trans_titles = []
                current_title = None
                for child in node.childNodes:
                    try:  #Some nodes (text and comments) have no tagName
                        tag = child.tagName
                    except AttributeError:
                        continue
                    if tag == 'trans-title':
                        if current_title is not None:
                            trans_titles.append((current_title, trans_subtitles))
                        current_title = child
                        trans_subtitles = []
                    elif tag == 'trans-subtitle':
                        trans_subtitles.append(child)
                    else:
                        break
                return trans_titles
            trans_title_tuple = namedtuple('trans_title',
                                           'content_type, id, xml_lang, node, subtitle')
            trans_titles = []
            for title, subtitle in iter_get_trans_titles(title_grp):
                #title is a single node, subtitle is a nodelist
                content_type = title.getAttribute('content_type')
                id = title.getAttribute('id')
                xml_lang = title.getAttribute('xml:lang')
                trans_titles.append(trans_title_tuple(content_type, id,
                                                      xml_lang, title,
                                                      subtitle))

        elif self.dtd_version == 3.0:
            trans_title_group_tuple = namedtuple('trans_title_group', 'trans_title, trans_subtitle')
            trans_titles = None
            trans_title_groups = []
            for trans_title_group in element_methods.get_children_by_tag_name('trans-title-group', title_grp):
                content_type = trans_title_group.getAttribute('content_type')
                id = trans_title_group.getAttribute('id')
                xml_lang = trans_title_group.getAttribute('xml:lang')
                trans_title_el = element_methods.get_optional_child('trans-title', trans_title_group)
                if not trans_title_el:
                    raise JPTSInputError('Missing mandatory trans-title in trans-title-group')
                trans_title = self.pack_node(trans_title_el,
                                             get_attrs=['content-type', 'id', 'xml:lang'],
                                             get_self=True)
                trans_subtitles = element_methods.get_children_by_tag_name('trans-subtitle', trans_title_group)
                trans_title_groups.append(trans_title_group_tuple(trans_title, trans_subtitles))
        
        title_group = title_grp_tuple(article_title, subtitles, trans_titles,
                                      trans_title_groups, alt_titles, fn_group)
        return title_group

    def extract_contrib_group(self):
        """
        <contrib-group> is defined under <article-meta> as 0 or more for all
        DTD versions. It has a very complex content model with many elements,
        perhaps most importantly <contrib>.

        The underlying <contrib> elements share all of the same elements as the
        <contrib> group, plus a few more added elements and attributes. A
        decision has been made here, as in previous code versions, to allow the
        child <contrib> elements to inherit the values of the parent
        <contrib-group>'s sub-elements (where said elements are held in common)
        as a reasonable assumption that values given to the group are intended
        to apply to each member. If the child <contrib> possesses its own
        instance of any of the elements, the value of those elements will
        override the default value given to it by its parent <contrib-group>.
        The exception to this rule is the value of the element attribute 'id',
        which would be inappropriate to share between elements.
        """
        contrib_group_tuple = namedtuple('contrib_group', 'content_type, id, \
contrib, address, aff, author_comment, bio, email, ext_link, uri, \
on_behalf_of, role, xref')
        
        contrib_grps = element_methods.get_children_by_tag_name('contrib-group', self.article_meta)
        
        for contrib_grp in contrib_grps:
            #Get the address content
            addresses = []
            for address in element_methods.get_children_by_tag_name('address', contrib_grp):
                #Packing an address is sufficiently complex to have its own method
                address.append(self.pack_address(address))
            affs = []
            for aff in element_methods.get_children_by_tag_name('aff', contrib_grp):
                affs.append(self.pack_node(aff,
                                           get_attrs=['content_type', 'id',
                                                      'rid'],
                                           get_self=True))
            
        

    def pack_node(self, node, get_child=None, get_childlist=None,
                  get_attrs=None, get_text=False, get_self=False):
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
        if get_self:
            field_names.append('node')
            field_vals.append(node)
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

        data_tuple = namedtuple(coerce_string(node.tagName), ', '.join([coerce_string(i) for i in field_names]))
        return data_tuple(*field_vals)

    def pack_address(self, address):
        """
        This method is used to package an address node into a tiered namedtuple
        structure.
        """
        address_tuple = namedtuple('address', 'addr_line, country, fax, \
institution, phone, email, ext_link, uri')
        addr_lines = []
        for addr_line in element_methods.get_children_by_tag_name('addr-line', address):
            addr_lines.append(self.pack_node(addr_line,
                                             get_attrs['content-type'],
                                             get_self=True))
        countries = []
        for country in element_methods.get_children_by_tag_name('country', address):
            countrys.append(self.pack_node(country,
                                           get_attrs=['content-type', 'country'],
                                           get_text=True))
        faxes = []
        for fax in element_methods.get_children_by_tag_name('fax', address):
            faxes.append(self.pack_node(fax,
                                        get_attrs=['content-type'],
                                        get_text=True))
        institutions = []
        for institutions in element_methods.get_children_by_tag_name('institution', address):
            institutions.append(self.pack_node(institution,
                                               get_attrs=['content-type', 'id',
                                                          'xlink:actuate',
                                                          'xlink:href',
                                                          'xlink:role',
                                                          'xlink:show',
                                                          'xlink:title',
                                                          'xlink:type',
                                                          'xmlns:xlink'],
                                               get_childlist=['sub', 'sup'],
                                               get_text=True,
                                               get_self=True))
        phones = []
        for phone in element_methods.get_children_by_tag_name('phone', address):
            phones.append(self.pack_node(phone,
                                         get_attrs=['content-type'],
                                         get_text=True))
        emails = []
        for email in element_methods.get_children_by_tag_name('email', address):
            emails.append(self.pack_node(email,
                                         get_attrs=['content-type',
                                                    'specific-use',
                                                    'xlink:actuate',
                                                    'xlink:href',
                                                    'xlink:role',
                                                    'xlink:show',
                                                    'xlink:title',
                                                    'xlink:type',
                                                    'xmlns:xlink'],
                                         get_text=True))
        ext_links = []
        for ext_link in element_methods.get_children_by_tag_name('ext-link', address):
            ext_links.append(self.pack_node(ext_link,
                                            get_attrs=['ext-link-type',
                                                       'id',
                                                       'specific-use',
                                                       'xlink:actuate',
                                                       'xlink:href',
                                                       'xlink:role',
                                                       'xlink:show',
                                                       'xlink:title',
                                                       'xlink:type',
                                                       'xmlns:xlink'],
                                            get_self=True))
        uris = []
        for uri in element_methods.get_children_by_tag_name('uri', address):
            uris.append(self.pack_node(uri,
                                       get_attrs=['content-type',
                                                  'xlink:actuate',
                                                  'xlink:href',
                                                  'xlink:role',
                                                  'xlink:show',
                                                  'xlink:title',
                                                  'xlink:type',
                                                  'xmlns:xlink'],
                                       get_text=True))
        return address_tuple(addr_lines, countries, faxes, institutions,
                             phones, emails, ext_links, uris)

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