# -*- coding: utf-8 -*-
"""
This module contains classes representing metadata in the Journal Publishing
Tag Set. There is a base class providing a baseline of functionality for the
JPTS and derived classes for distinct versions of the Tag Set. With this
implementation, the commonalities between versions may be presented in the base
class while their differences may be presented in their derived classes. An
important distinction must to be made between publisher and the DTD version.
For full extensibility in development, DTD and publisher parameters must be
recognized for their distinct roles in the format of a document. As a class for
metadata, this class will handle everything except <body>.
"""

from collections import namedtuple
import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
import openaccess_epub.jpts.jptscontrib as jptscontrib
import logging

log = logging.getLogger('JPTSMetaData')


class JPTSMetaData(object):
    """
    This is the base class for the Journal Publishing Tag Set metadata.
    """
    def __init__(self, document, publisher):
        log.info('Instantiating JPTSMetaData{0} class'.format(self.dtdVersion()))
        self.doc = document
        self.publisher_name = publisher
        self.get_top_elements()
        self.get_front_elements()
        self.parse_journal_metadata()
        self.parse_article_metadata()
        self.parse_back_data()

    def get_top_elements(self):
        self.front = self.doc.getElementsByTagName('front')[0]  # Required
        try:
            self.back = self.doc.getElementsByTagName('back')[0]  # Optional
        except IndexError:
            self.back = None
        #sub-article and response are mutually exclusive, optional, 0 or more
        self.sub_article = self.doc.getElementsByTagName('sub-article')
        if self.sub_article:
            self.response = None
        else:
            self.sub_article = None
            self.response = self.doc.getElementsByTagName('response')
            if not self.response:
                self.response = None
        self.floats_wrap = self.get_top_floats_wrap()  # relevant to v2.3
        self.floats_group = self.get_top_floats_group()  # relevant to v3.0

    def get_top_floats_wrap(self):
        return None

    def get_top_floats_group(self):
        return None

    def get_front_elements(self):
        """
        The structure of elements under <front> is the same for all versions
        (2.0, 2.3, 3.0). <journal-meta> and <article-meta> are required,
        <notes> is zero or one.
        """
        self.journal_meta = self.front.getElementsByTagName('journal-meta')[0]
        self.article_meta = self.front.getElementsByTagName('article-meta')[0]
        try:
            self.notes = self.front.getElementsByTagName('notes')[0]
        except IndexError:
            self.notes = None

    def parse_journal_metadata(self):
        """
        As the specifications for metadata under the <journal-meta> element
        vary between version, this class will be overridden by the derived
        classes. <journal-meta> stores information about the journal in which
        the article is found.
        """
        return None

    def get_journal_id(self):
        """
        <journal-id> is a required, one or more, sub-element of <journal-meta>.
        It can only contain text, numbers, or special characters. It has a
        single potential attribute, 'journal-id-type', whose value is used as a
        key to access the text data of its tag.
        """
        ids = {}
        for j in self.journal_meta.getElementsByTagName('journal-id'):
            text = utils.nodeText(j)
            ids[j.getAttribute('journal-id-type')] = text
        return ids

    def get_ISSN(self):
        """
        <issn> is a required, one or more, sub-element of <journal-meta>. It
        can only contain text, numbers, or special characters. It has a single
        potential attribute, 'pub-type', whose value is used as a key to access
        the text data of its tag.
        """
        issns = {}
        for i in self.journal_meta.getElementsByTagName('issn'):
            text = utils.nodeText(i)
            issns[i.getAttribute('pub-type')] = text
        return issns

    def get_publisher(self):
        """
        <publisher> under <journal-meta> is an optional tag, zero or one, which
        under some DTD versions has the attribute 'content-type'. If it exists,
        it contains one <publisher-name> element which contains only text,
        numbers, or special characters. It also may include one <publisher-loc>
        element which has text, numbers, special characters, and the address
        linking elements <email>, <ext-link>, and <uri>. This function returns
        the publisher information as a namedtuple for simple access.
        """
        pd = namedtuple('Publisher', 'name, loc, content_type')
        pub_node = self.journal_meta.getElementsByTagName('publisher')
        if pub_node:
            content_type = pub_node[0].getAttribute('content-type')
            if not content_type:
                content_type = None
            name = pub_node[0].getElementsByTagName('publisher-name')[0]
            name = utils.nodeText(name)
            try:
                loc = pub_node[0].getElementsByTagName('publisher-loc')[0]
            except IndexError:
                loc = None
            else:
                if self.dtdVersion() == '2.0':
                    loc = utils.nodeText(loc)
            return pd(name, loc, content_type)
        else:
            return pd(None, None, None)

    def get_journal_meta_notes(self):
        """
        The <notes> tag under the <journal-meta> is option, zero or one, and
        has attributes 'id' and 'notes-type'. This tag has complex content and
        unknown use cases. For now, this node will simply be collected but not
        processed at this level.
        """
        try:
            tag = self.journal_meta.getElementsByTagName('notes')[0]
        except IndexError:
            return None
        else:
            return tag

    def parse_article_metadata(self):
        """
        As the specifications for metadata under the <article-meta> element
        vary between version, this class will be overridden by the derived
        classes. <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        return None

    def get_article_id(self):
        """
        <article-id> is an optional, 0 or more, sub-element of <article-meta>.
        It can only contain text, numbers, or special characters. It has a
        single potential attribute, 'pub-id-type', whose value is used as a
        key to access the text data of its tag.
        """
        ids = {}
        for j in self.article_meta.getElementsByTagName('article-id'):
            text = utils.nodeText(j)
            ids[j.getAttribute('pub-id-type')] = text
        return ids

    def get_article_categories(self):
        """
        The <article-categories> tag is optional, zero or one, underneath the
        <article-meta> tag. It's specification is the same in each DTD. It can
        contain zero or more of each of the following elements in order:
        <subj-group>, <series-title>, and <series-text>. Beyond this level of
        detail, much is left up to the publisher. The <article-categories> node
        will be captured if it exists and can be operated on publisher-wise as
        needed.
        """
        try:
            a = self.article_meta.getElementsByTagName('article-categories')[0]
        except IndexError:
            return None
        else:
            return a

    def get_title_group(self):
        """
        <title-group> is a required element underneath the <article-meta> tag.
        Below this level, each specification has its own way of constructing
        its title elements.
        """
        return self.article_meta.getElementsByTagName('title-group')[0]

    def get_contrib_group(self):
        """
        <contrib-group> is an optional, zero or more, element used to group
        elements used to represent individuals who contributed independently
        to the article. It is not to be confused with <collab>. Beneath this
        element, it may contain <contrib> elements for individual authors or
        editors. It may also contain many of the elements contained within
        <contrib> elements. Should these elements exist, they are presumably
        pertinent to all <contrib> members contained, and will be applied to
        those elements unless overridden during their inspection. See
        jptscontrib.py for further information.
        """
        contrib_group_list = []
        for each in self.article_meta.getElementsByTagName('contrib-group'):
            contrib_group_list.append(jptscontrib.ContribGroup(each))
        return contrib_group_list

    def get_aff(self):
        """
        <aff> is an optional tag that can be contained in <article-meta>,
        <collab>, <contrib>, <contrib-group>, <person-group>, and (in the case
        of v2.3 and v3.0) <front-stub>. It's potential attributes are id, rid,
        and content-type. It is commonly referred to by other elements, thus it
        is important to make its attributes accessible. It's contents are
        diverse, but they include the address elements which may feature
        heavily.
        """
        affs = element_methods.get_children_by_tag_name('aff', self.article_meta)
        affsbyid = {}
        for aff in affs:
            aid = aff.getAttribute('id')
            affsbyid[aid] = aff
        return affs, affsbyid

    def get_author_notes(self):
        """
        <author-notes> is an optional tag, 0 or 1, for each DTD and has the
        same potential attributes, id and rid. It may include an optional
        <title> element (<label> is included in v3.0), and one or more of any
        of the following: <fn>, <corresp>, (<p> in v3.0).
        """
        try:
            return self.article_meta.getElementsByTagName('author-notes')[0]
        except IndexError:
            return None

    def get_pub_date(self):
        """
        <pub-date> is a mandatory element, 1 or more, within the <article-meta>
        element. It has a single attribute, pub-type, and its content model is:
        (((day?, month?) | season)?, year)
        This is common between DTD versions. This method returns a dictionary
        of namedtuples whose keys are the values of the pub-type attribute.
        """
        pd = namedtuple('Pub_Date', 'Node, year, month, day, season, pub_type')
        pub_dates = {}
        for k in self.article_meta.getElementsByTagName('pub-date'):
            try:
                s = k.getElementsByTagName('season')[0]
            except IndexError:
                season = ''
                try:
                    m = k.getElementsByTagName('month')[0]
                except IndexError:
                    month = 0
                else:
                    month = utils.nodeText(m)
                try:
                    d = k.getElementsByTagName('day')[0]
                except IndexError:
                    day = 0
                else:
                    day = utils.nodeText(d)
            else:
                season = utils.nodeText(s)
                month = 0
                day = 0
            y = k.getElementsByTagName('year')[0]
            year = utils.nodeText(y)
            pub_type = k.getAttribute('pub-type')
            pub_dates[pub_type] = pd(k, year, month, day, season, pub_type)
        return pub_dates

    def get_volume_id(self):
        """
        <volume-id> is an optional element, 0 or more, with the optional
        attributes pub-id-type and content-type (only in v2.3 and v3.0). It is
        used to record a name or an identifier, such as a DOI, that describes
        an entire volume of a journal. This method will return the text data of
        the nodes in a dictionary keyed to pub-id-type values.
        """
        vol_ids = {}
        for vi in element_methods.get_children_by_tag_name('volume-id', self.article_meta):
            text = utils.nodeText(vi)
            vol_ids[vi.getAttribute('pub-id-type')] = text
        return vol_ids

    def get_issue_id(self):
        """
        <issue-id> is an optional element, 0 or more, with the optional
        attributes pub-id-type and content-type (only in v2.3 and v3.0). It is
        used to record a name or identifier, such as a DOI, that describes an
        entire issue of a journal This method will return the text data of the
        nodes in a dictionary keyed to pub-id-type values.
        """
        iss_ids = {}
        for ii in self.article_meta.getElementsByTagName('issue-id'):
            text = utils.nodeText(ii)
            iss_ids[ii.getAttribute('pub-id-type')] = text
        return iss_ids

    def get_issueTitle(self):
        """
        <issue-title> is an optional element, 0 or more, which contains only
        text, numbers, special characters. In versions 2.3 and 3.0, it has an
        optional attribute of content-type. Each node's text will be collected
        into a list, later implementation may use the content-type attribute.
        """
        issue_titles = []
        for it in self.article_meta.getElementsByTagName('issue-title'):
            issue_titles.append(utils.nodeText(it))
        return issue_titles

    def get_supplement(self):
        """
        <supplement> element exists as an optional element, 0 or 1, within
        <article-meta>. It can also be found in other descendants of
        <article-meta>; <product> and <related-article>. Its content is varied
        and depends on DTD version. At this stage, we merely collect the node.
        """
        try:
            s = element_methods.get_children_by_tag_name('supplement', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return s

    def get_fpage(self):
        """
        <fpage> is a mandatory element if <elocation-id> is not included within
        <article-meta>. There will be only one. Its only attribute in v2.0 is
        seq, while v2.3 and v3.0 also provide content-type. Its only content
        is text, numbers, and special characters.
        """
        fp = namedtuple('fpage', 'text, seq')
        fpage = element_methods.get_children_by_tag_name('fpage', self.article_meta)[0]
        text = utils.nodeText(fpage)
        seq = fpage.getAttribute('seq')
        return fp(text, seq)

    def get_lpage(self):
        """
        <lpage> is an optional, 0 or 1, element if <elocation-id> is not
        present within <article-meta>. Its only attribute is content-type
        with DTD versions 2.3 and 3.0. Its only content is text, numbers, and
        special characters.
        """
        try:
            lpage = element_methods.get_children_by_tag_name('lpage', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return utils.nodeText(lpage)

    def get_page_range(self):
        """
        <page-range> is an optional, 0 or 1, element if <elocation-id> is not
        present within <article-meta>. Its only attribute is content-type with
        DTD versions 2.3 and 3.0. It's only content is text, numbers, and
        special characters. It should be noted, that <page-range> supplements
        <fpage> and <lpage>, it does not replace them.
        """
        try:
            pr = element_methods.get_children_by_tag_name('page-range', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return utils.nodeText(pr)

    def get_elocation_id(self):
        """
        <elocation-id> is an optional, 0 or 1, which is mutually exclusive with
        <fpage>, <lpage>, and <page-range>. Its only attribute in v2.0 is seq,
        while v2.3 and v3.0 also provide content-type. Its content is text,
        numbers, and special characters.
        """
        try:
            e = element_methods.get_children_by_tag_name('elocation-id', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return utils.nodeText(e)

    def get_email(self):
        """
        <email> is an optional element, 0 or more, in <article-meta>. Its only
        content is text, numbers, and special characters. It has attributes
        common to each version of the JPTS, and content-type is provided by
        v2.3 and v3.0. For now, this method will simply collect a list of
        <email> nodes directly under <article-meta>.
        """
        return element_methods.get_children_by_tag_name('email', self.article_meta)

    def get_ext_link(self):
        """
        <ext-link> is an optional element, 0 or more, in <article-meta>. It may
        contain text and various formatting and emphasis elements. It has
        the following possible attributes: ext-link-type, id, xlink:actuate,
        xlink:href, xlink:role, xlink:show, xlink:title, xlink:type, and
        xmlns:xlink in v2.0 and v2.3. v3.0 add specific-use. For now, this
        method will simply collect a list of <ext-link> nodes directly under
        <article-meta>.
        """
        return element_methods.get_children_by_tag_name('ext-link', self.article_meta)

    def get_URI(self):
        """
        <uri> is an optional element, 0 or more, in <article-meta>. It may only
        contain text, numbers, and special characters. It has the following
        possible attributes: xlink:href, xlink:role, xlink:show, xlink:title,
        xlink:type, and xmlns:xlink (in v2.0). v2.3. v3.0 add content-type. For
        now, this method will simply collect a list of <uri> nodes directly
        under <article-meta>.
        """
        return element_methods.get_children_by_tag_name('uri', self.article_meta)

    def get_product(self):
        """
        <product> is an optional element, 0 or more, in <article-meta> that has
        a huge range for potential content. Use cases are likely to depend
        heavily on publishers. For now the nodes will be collected into a list.
        The following attributes are possible: id (not in v2.0), product-type,
        xlink:href, xlink:role, xlink:show, xlink:title, xlink:type,
        and xmlns:xlink.
        """
        return element_methods.get_children_by_tag_name('product', self.article_meta)

    def get_supplementary_material(self):
        """
        <supplementary-material> is an optional element, 0 or more, in
        <article-meta> to be used to 'alert to the existence of
        supplementary material and so that it can be accessed from the
        article'. The use cases will depend heavily on publishers and it will
        take some effort to fully support. For now, the nodes will merely be
        collected.
        """
        return element_methods.get_children_by_tag_name('supplementary-material', self.article_meta)

    def get_history(self):
        """
        The <history> element is optional, 0 or 1, within <article-meta> and
        will contain 1 or more <date> elements. This content describes dates
        related to the processing history of the document. Based on the content
        model for this element and the <date> elements it contains, the history
        will be represented as a dictionary of dates keyed by date-type values.
        """
        dates = {'received': None, 'accepted': None}
        datetuple = namedtuple('Date', 'year, month, day, season')
        try:
            h = element_methods.get_children_by_tag_name('history', self.article_meta)[0]
        except IndexError:
            return dates
        else:
            for k in element_methods.get_children_by_tag_name('date', h):
                try:
                    s = k.getElementsByTagName('season')[0]
                except IndexError:
                    season = ''
                    try:
                        m = k.getElementsByTagName('month')[0]
                    except IndexError:
                        month = 0
                    else:
                        month = utils.nodeText(m)
                    try:
                        d = k.getElementsByTagName('day')[0]
                    except IndexError:
                        day = 0
                    else:
                        day = utils.nodeText(d)
                else:
                    season = utils.nodeText(s)
                    month = 0
                    day = 0
                y = k.getElementsByTagName('year')[0]
                year = utils.nodeText(y)
                dt = k.getAttribute('date-type')
                dates[dt] = datetuple(year, month, day, season)
        return dates

    def get_copyright_statement(self):
        """
        <copyright-statement> is an optional, 0 or 1, element in <article-meta>
        which can contain text, address linking elements, and formatting
        elements. This method will return the node if it exists. In version 2.3
        it is best practice to put the <copyright-statement> element and its
        information within the <permissions> tag.
        """
        try:
            cs = element_methods.get_children_by_tag_name('copyright-statement', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return cs

    def get_copyright_year(self):
        """
        <copyright-year> is an optional, 0 or 1, element in <article-meta>
        which may contain only text, numbers, and special characters. If the
        node exists, this method will return the text data it contains as a
        string. In version 2.3 it is best practice to put the <copyright-year>
        element and its information within the <permissions> tag.
        """
        try:
            cy = element_methods.get_children_by_tag_name('copyright-year', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return utils.nodeText(cy)

    def get_license(self):
        """
        <license> is an optional, 0 or 1, element in <article-meta> which may
        have one or more <p> elements inside. In version 2.3 and, it is
        not good practice for this element to be found under <article-meta> but
        rather inside the <permissions> element. It does not exist outside the
        <permissions> element in version 3.0. The usage will vary between
        publishers, so it is best to keep aware that the license information
        may be found in either location. The possible attributes are
        license-type and the xlink/xmlns attributes. This will return a
        namedtuple of the node alongside it's license-type value.
        """
        lic = namedtuple('license', 'node, license_type')
        try:
            l = element_methods.get_children_by_tag_name('license', self.article_meta)[0]
        except IndexError:
            return None
        else:
            return lic(l, l.getAttribute('license-type'))

    def get_permissions(self):
        """
        The <permissions> element is not used in version 2.0. It is an optional
        element, 0 or 1, in versions 2.3 and 3.0, where it may hold 0 or 1 of
        each of the following, <copyright-statement>, <copyright-year>,
        <copyright-holder>, and <license>. This method will return a namedtuple
        to provide named access to each of these elements.
        """
        perm = namedtuple('Permissions', 'statement, year, holder, license, license_type')
        try:
            p = element_methods.get_children_by_tag_name('permissions', self.article_meta)[0]
        except IndexError:
            return None
        else:
            nodes = []
            for node_name in ['copyright-statement', 'copyright-year',
                              'copyright-holder', 'license']:
                try:
                    nodes.append(element_methods.get_children_by_tag_name(node_name, p)[0])
                except IndexError:
                    nodes.append(None)
            if nodes[3]:
                nodes.append(nodes[3].getAttribute('license-type'))
            return perm(*nodes)

    def get_self_URI(self):
        """
        The <self-uri> element is optional, 0 or more, within the
        <article-meta> and may only contain text, numbers, or special
        characters. Usage will vary by publisher, and any implementation at
        that time should be determined by that publisher's usage. This method
        will only collect the nodes.
        """
        return element_methods.get_children_by_tag_name('self-uri', self.article_meta)

    def get_related_article(self):
        """
        <related-article> is an optional element, 0 or more, within
        <article-meta>. This element is not likely to be critical to displaying
        the article content, but is valuable as a link to other content. This
        element allows for the inclusion of various metadata about the related
        content and should provide sufficient instruction (perhaps with some
        implicit assumptions based on the publisher) to construct a link to
        the resource. This element is of significant interest, but as the
        content shall vary widely between publishers, and perhaps the related
        content itself, the parsing of this element will not be executed at
        this stage for now.
        """
        return element_methods.get_children_by_tag_name('related-article', self.article_meta)

    def get_abstract(self):
        """
        <abstract> is an optional element, 0 or more, within <article-meta>.
        Its potential attributes varies between DTD versions; abstract-type
        and xml:lang are present in all versions, while id exists only in 2.3
        and 3.0, only 3.0 has specific-use. The <abstract> nodes will be
        collected along with the attribute values into a list of namedtuples.
        """
        abstracts = []
        abst = namedtuple('Abstract', 'node, type, xml_lang, id, specific_use')
        for a in element_methods.get_children_by_tag_name('abstract', self.article_meta):
            atyp = a.getAttribute('abstract-type')
            lang = a.getAttribute('xml:lang')
            abid = a.getAttribute('id')
            spec = a.getAttribute('specific-use')
            abstracts.append(abst(a, atyp, lang, abid, spec))
        return abstracts

    def get_trans_abstract(self):
        """
        <trans-abstract> is similar in all respects to <abstract> and is used
        to store the abstract in a language other than the original publication
        language.
        """
        trans_abstracts = []
        tab = namedtuple('Trans_Abstract', 'node, type, xml_lang, id, specific_use')
        for ta in element_methods.get_children_by_tag_name('trans-abstract', self.article_meta):
            atyp = ta.getAttribute('abstract-type')
            lang = ta.getAttribute('xml:lang')
            abid = ta.getAttribute('id')
            spec = ta.getAttribute('specific-use')
            trans_abstracts.append(abs(ta, atyp, lang, abid, spec))
        return trans_abstracts

    def get_kwd_group(self):
        """
        <kwd-group> is an optional element, 0 or more, in <article-meta> which
        may contain 0 or 1 <title> elements and 1 or more <kwd> elements. Note
        that this method is overridden in the derived JPTSMetaData30 to account for
        <compound-kwd> elements. The content of <kwd> elements includes text,
        numbers, special characters, and emphasis elements. The potential
        attributes are id, kwd-group-type, and xml:lang. This method will
        return a list of <kwd-group> nodes, as well as a list of all <kwd>
        nodes tupled to their id attribute values and an inherited type from
        their parent <kwd-group> kwd-group-type attribute value
        """
        kwd_groups = []  # There may be more than one
        all_kwds = []  # A list of all keywords
        kwd = namedtuple('Keyword', 'node, type, id')
        for kg in self.article_meta.getElementsByTagName('kwd-group'):
            kwd_groups.append(kg)
            ktype = kg.getAttribute('keyword-group-type')
            for key in kg.getElementsByTagName('kwd'):
                kid = key.getAttribute('id')
                all_kwds.append(kwd(key, ktype, kid))
        return kwd_groups, all_kwds

    def get_contract_num(self):
        """
        <contract-num> is an optional element, 0 or more, in <article-meta>
        which may only contain text, numbers, or special characters, though it
        may have various attributes. This method will return a list of tuples
        containing the nodes, their text, and their salient attributes. If
        necessary, more robust handling of all attributes may be added.
        """
        con_nums = []
        cn = namedtuple('Contract_Num', 'node, text, id, rid')
        for c in element_methods.get_children_by_tag_name('contract-num', self.article_meta):
            text = utils.nodeText(c)
            cid = c.getAttribute('id')
            crid = c.getAttribute('rid')
            con_nums.append(cn(c, text, cid, crid))
        return con_nums

    def get_contract_sponsor(self):
        """
        <contract-sponsor> is an optional element, 0 or more, in <article-meta>
        which may have complex publisher-dependent content. This method will
        return a list of the nodes.
        """
        return element_methods.get_children_by_tag_name('contract-sponsor', self.article_meta)

    def get_conference(self):
        """
        <conference> is an optional element, 0 or more, in <article-meta> which
        is used to describe a conference at which the article was originally
        presented. Technically, it would appear acceptable to name any number
        of conferences.
        """
        conferences = []
        conf = namedtuple('Conference', 'date, name, acronym, num, loc, sponsor, theme')
        for c in element_methods.get_children_by_tag_name('conference', self.article_meta):
            date = utils.nodeText(c.getElementsByTagName('conf-date')[0])
            try:
                n = c.getElementsByTagName('conf-name')[0]
            except IndexError:
                name = None
            else:
                name = utils.nodeText(n)
            try:
                a = c.getElementsByTagName('conf-acronym')[0]
            except IndexError:
                acronym = None
            else:
                acronym = utils.nodeText(a)
            if not name and not acronym:
                print('Warning: Conference element provides no name or acronym')
            try:
                cn = c.getElementsByTagName('conf-num')[0]
            except IndexError:
                num = None
            else:
                num = utils.nodeText(cn)
            try:
                l = c.getElementsByTagName('conf-loc')[0]
            except IndexError:
                loc = None
            else:
                loc = utils.nodeText(l)
            try:
                s = c.getElementsByTagName('conf-sponsor')[0]
            except IndexError:
                spo = None
            else:
                spo = utils.nodeText(s)
            try:
                theme = c.getElementsByTagName('conf-theme')[0]
            except IndexError:
                theme = None
            conferences.append(date, name, acr, num, loc, spo, theme)
        return conferences

    def get_counts(self):
        """
        <counts> is an optional element, 0 or 1, in <article-meta>, which
        provides a container for several <count>-type elements. Each of these
        elements is empty, and has the attribute count.
        """
        counts = {'fig-count': None, 'table-count': None, 'equation-count':
                  None, 'ref-count': None, 'page-count': None, 'word-count':
                  None}
        try:
            cnode = self.article_meta.getElementsByTagName('counts')[0]
        except IndexError:
            return {}
        for ckey in counts:
            try:
                _node = cnode.getElementsByTagName(ckey)[0]
            except IndexError:
                pass
            else:
                counts[ckey] = _node.getAttribute('count')
        return counts

    def get_custom_meta_wrap(self):
        """
        <custom-meta-wrap> is an optional element, 0 or more, in <article-meta>
        which is designed as a built-in structure for metadata not supported by
        the DTD. <custom-meta> elements can be listed here, which in turn
        contain pairs of <meta-name> and <meta-value>. Contents vary between
        DTDs and I expect that there would be significant variation between
        publishers. At this point, this method only endeavors to return a list
        of the <custom-meta-wrap> nodes.
        """
        return element_methods.get_children_by_tag_name('custom-meta-wrap', self.article_meta)

    def parse_back_data(self):
        """
        For each version of the JPTS, <back> contains "Ancillary or supporting
        material that, although it is not included as part of the main
        narrative flow of a journal article, is published with the article, for
        example, an appendix, glossary, or bibliographic reference list."
        The content elements are common between versions, except for <label>
        which is optional, 0 or 1, only in version 3.0
        """
        return None

    def dtd_version(self):
        return ''


class JPTSMetaData20(JPTSMetaData):
    """
    This is the derived class for version 2.0 of the Journal Publishing Tag Set
    metadata.
    """

    def parse_journal_metadata(self):
        """
        <journal-meta> stores information about the journal in which
        the article is found.
        """
        jm = self.journal_meta  # More compact
        #There will be one or more <journal-id> elements, which will be indexed
        #in a dictionary by their 'journal-id-type' attributes
        self.journal_id = self.get_journal_id()
        #<journal-title> is zero or more and has no attributes
        self.journal_title = []
        for jt in jm.getElementsByTagName('journal-title'):
            self.journal_title.append(utils.nodeText(jt))
        #<abbrev-journal-title> is zero or more and has 'abbrev-type' attribute
        self.abbrev_journal_title = {}
        for a in jm.getElementsByTagName('abbrev-journal-title'):
            text = utils.nodeText(a)
            self.abbrev_journal_title[a.getAttribute('abbrev-type')] = text
        #<issn> is one or more and has 'pub-type' attribute
        self.issn = self.get_ISSN()
        self.publisher = self.get_publisher()  # publisher.loc is text
        self.jm_notes = self.get_journal_meta_notes()

    def parse_article_metadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        am = self.article_meta  # More compact
        #There will be zero or more <article-id> elements whose text data will
        #by indexed by their pub-id-type attribute values
        self.article_id = self.get_article_id()
        self.article_categories = self.get_article_categories()
        self.title_group = self.get_title_group()
        #self.title will be a namedtuple comprised of the elements under
        #<title-group>. names will be set by their elements, and values will
        #be set by the following types
        #article_title : Node
        #subtitle      : NodeList
        #trans-title   : dictionary[xml:lang]
        #alt-title     : dictionary[alt-title-type]
        #fn_group      : Node
        atg = namedtuple('Article_Title_Group', 'article_title, subtitle, trans_title, alt_title, fn_group')
        article = self.title_group.getElementsByTagName('article-title')[0]
        subtitle = self.title_group.getElementsByTagName('subtitle')
        trans = {}
        for t in self.title_group.getElementsByTagName('trans-title'):
            trans[t.getAttribute('xml:lang')] = t
        alt = {}
        for a in self.title_group.getElementsByTagName('alt-title'):
            alt[a.getAttribute('alt-title-type')] = a
        try:
            fn = self.title_group.getElementsByTagName('fn-group')[0]
        except IndexError:
            fn = None
        self.title = atg(article, subtitle, trans, alt, fn)
        self.contrib_group = self.get_contrib_group()
        self.contrib = []
        for each in self.contrib_group:
            self.contrib += each.contributors()
        self.affs, self.affs_by_id = self.get_aff()
        self.author_notes = self.get_author_notes()
        self.pub_date = self.get_pub_date()
        #This segment gets None or a text value for self.volume
        try:
            vol = element_methods.get_children_by_tag_name('volume', am)[0]
        except IndexError:
            self.volume = None
        else:
            self.volume = utils.nodeText(vol)
        self.volume_id = self.get_volume_id()
        #This segment gets None or a text value for self.issue
        try:
            iss = element_methods.get_children_by_tag_name('issue', am)[0]
        except IndexError:
            self.issue = None
        else:
            self.issue = utils.nodeText(iss)
        self.issue_id = self.get_issue_id()
        self.supplement = self.get_supplement()
        #Get values for elocation_id, fpage, lpage, and page_range
        self.elocation_id = self.get_elocation_id()
        if self.elocation_id:
            self.fpage = None
            self.lpage = None
            self.page_range = None
        else:
            self.fpage = self.get_fpage()
            self.lpage = self.get_lpage()
            self.page_range = self.get_page_range()
        self.email = self.get_email()
        self.ext_link = self.get_ext_link()
        self.uri = self.get_URI()
        self.product = self.get_product()
        self.supplementary_material = self.get_supplementary_material()
        self.history = self.get_history()
        self.copyright_statement = self.get_copyright_statement()
        self.copyright_year = self.get_copyright_year()
        self.license = self.get_license()
        self.self_uri = self.get_self_URI()
        self.related_article = self.get_related_article()
        self.abstract = self.get_abstract()
        self.trans_abstract = self.get_trans_abstract()
        self.kwd_group, self.all_kwds = self.get_kwd_group()
        self.contract_num = self.get_contract_num()
        self.contract_sponsor = self.get_contract_sponsor()
        self.conference = self.get_conference()
        self.counts = self.get_counts()
        self.custom_meta_wrap = self.get_custom_meta_wrap()

    def dtd_version(self):
        return '2.0'


class JPTSMetaData23(JPTSMetaData):
    """
    This is the derived class for version 2.3 of the Journal Publishing Tag Set
    metadata.
    """

    def get_top_floats_wrap(self):
        """
        <floats-wrap> may exist as a top level element for DTD v2.3. This
        tag may only exist under <article>, <sub-article>, or <response>.
        This function will only return a <floats-wrap> node underneath article,
        the top level element.
        """
        floats_wrap = self.doc.getElementsByTagName('floats-wrap')
        for fw in floats_wrap:
            if fw.parentNode.tagName == 'article':
                return fw
        return None

    def parse_journal_metadata(self):
        """
        <journal-meta> stores information about the journal in which
        the article is found.
        """
        jm = self.journal_meta  # More compact
        #There will be one or more <journal-id> elements, which will be indexed
        #in a dictionary by their 'journal-id-type' attributes
        self.journal_id = self.get_journal_id()
        #<journal-title> is zero or more and has 'content-type' attribute
        self.journal_title = {}
        for jt in jm.getElementsByTagName('journal-title'):
            text = utils.nodeText(jt)
            self.journal_title[jt.getAttribute('content-type')] = text
        #<journal-subtitle> is zero or more and has 'content-type' attribute
        self.journal_subtitle = {}
        for js in jm.getElementsByTagName('journal-subtitle'):
            text = utils.nodeText(js)
            self.journal_subtitle[js.getAttribute('content-type')] = text
        #<trans-title> is zero or more and has the attributes: 'content-type',
        #'id', and 'xml:lang'
        #For now, these nodes will be simply be collected
        self.trans_title = jm.getElementsByTagName('trans-title')
        #<trans-subtitle> is zero or more and has the attributes:
        #'content-type', 'id', and 'xml:lang'
        #As with <trans-title>, these nodes will be simply be collected
        self.trans_subtitle = jm.getElementsByTagName('trans-subtitle')
        #<abbrev-journal-title> is zero or more and has 'abbrev-type' attribute
        self.abbrev_journal_title = {}
        for a in jm.getElementsByTagName('abbrev-journal-title'):
            text = utils.nodeText(a)
            self.abbrev_journal_title[a.getAttribute('abbrev-type')] = text
        #<issn> is one or more and has 'pub-type' attribute
        self.issn = self.get_ISSN()
        self.publisher = self.get_publisher()  # publisher.loc is a node
        self.jm_notes = self.get_journal_meta_notes()

    def parse_article_metadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        am = self.article_meta  # More compact
        #There will be zero or more <article-id> elements whose text data will
        #by indexed by their pub-id-type attribute values
        self.article_id = self.get_article_id()
        self.article_categories = self.get_article_categories()
        self.title_group = self.get_title_group()
        #v2.3 has rather more potential attributes, which adds complexity to
        #The matter of indexing them, as is done in v2.0. I'm opting for making
        #composite elements of Nodes with their attribute values for easier
        #lookup
        #self.title will be a namedtuple comprised of the elements under
        #<title-group>. names will be set by their elements, and values will
        #be set by the following types
        #article_title  : Node
        #subtitle       : NodeList
        #trans-title    : [namedtuple(Node,attributes)]
        #trans-subtitle : [namedtuple(Node,attributes)]
        #alt-title      : dictionary[alt-title-type]
        #fn_group       : Node
        atg = namedtuple('Article_Title_Group', 'article_title, subtitle, trans_title, trans_subtitle, alt_title, fn_group')
        article = self.title_group.getElementsByTagName('article-title')[0]
        subtitle = self.title_group.getElementsByTagName('subtitle')
        #<trans-title> tags
        trans_title = []
        tt = namedtuple('trans_title', 'Node, content_type, id, xml_lang')
        for e in self.title_group.getElementsByTagName('trans-title'):
            ct = e.getAttribute('content-type')
            eid = e.getAttribute('id')
            xl = e.getAttribute('xml:lang')
            new = tt(e, ct, eid, xl)
            trans_title.append(new)
        #<trans-subtitle> tags
        trans_sub = []
        ts = namedtuple('trans_subtitle', 'Node, content_type, id, xml_lang')
        for e in self.title_group.getElementsByTagName('trans-subtitle'):
            ct = e.getAttribute('content-type')
            eid = e.getAttribute('id')
            xl = e.getAttribute('xml:lang')
            new = ts(e, ct, eid, xl)
            trans_sub.append(new)
        #<alt-title> tags
        alt = {}
        for a in self.title_group.getElementsByTagName('alt-title'):
            alt[a.getAttribute('alt-title-type')] = a
        #<fn-group> tag
        try:
            fn = self.title_group.getElementsByTagName('fn-group')[0]
        except IndexError:
            fn = None
        #Set self.title now
        self.title = atg(article, subtitle, trans_title, trans_sub, alt, fn)
        self.contrib_group = self.get_contrib_group()
        self.contrib = []
        for each in self.contrib_group:
            self.contrib += each.contributors()
        self.affs, self.affs_by_id = self.get_aff()
        self.author_notes = self.get_author_notes()
        self.pub_date = self.get_pub_date()
        self.volume = self.get_volume()
        self.volume_id = self.get_volume_id()
        self.issue = self.get_issue()
        self.issue_id = self.get_issue_id()
        self.supplement = self.get_supplement()
        #Get values for elocation_id, fpage, lpage, and page_range
        self.elocation_id = self.get_elocation_id()
        if self.elocation_id:
            self.fpage = None
            self.lpage = None
            self.page_range = None
        else:
            self.fpage = self.get_fpage()
            self.lpage = self.get_lpage()
            self.page_range = self.get_page_range()
        self.email = self.get_email()
        self.ext_link = self.get_ext_link()
        self.uri = self.get_URI()
        self.product = self.get_product()
        self.supplementary_material = self.get_supplementary_material()
        self.history = self.get_history()
        self.copyright_statement = self.get_copyright_statement()
        self.copyright_year = self.get_copyright_year()
        self.license = self.get_license()
        self.permissions = self.get_permissions()
        self.self_uri = self.get_self_URI()
        self.related_article = self.get_related_article()
        self.abstract = self.get_abstract()
        self.trans_abstract = self.get_trans_abstract()
        self.kwd_group, self.all_kwds = self.get_kwd_group()
        self.contract_num = self.get_contract_num()
        self.contract_sponsor = self.get_contract_sponsor()
        self.grant_num = self.get_grant_num()
        self.grant_sponsor = self.get_grant_sponsor()
        self.conference = self.get_conference()
        self.counts = self.get_counts()
        self.custom_meta_wrap = self.get_custom_meta_wrap()

    def get_volume(self):
        """
        This method operates on the optional, 0 or 1, element <volume>. Its
        potential attributes, seq and content-type will be extracted.
        """
        volume = namedtuple('Volume', 'value, seq, content_type')
        try:
            vol = element_methods.get_children_by_tag_name('volume', self.article_meta)[0]
        except IndexError:
            return None
        else:
            text = utils.nodeText(vol)
            seq = vol.getAttribute('seq')
            ct = vol.getAttribute('content-type')
            return volume(text, seq, ct)

    def get_issue(self):
        """
        This method operates on the optional, 0 or 1, element <issue>. Its
        potential attributes, seq and content-type will be extracted.
        """
        issue = namedtuple('Issue', 'value, seq, content_type')
        try:
            iss = element_methods.get_children_by_tag_name('issue', self.article_meta)[0]
        except IndexError:
            return None
        else:
            text = utils.nodeText(iss)
            seq = iss.getAttribute('seq')
            ct = iss.getAttribute('content-type')
            return issue(text, seq, ct)

    def get_grant_num(self):
        """
        <grant-num> is an optional element, 0 or more, in <article-meta> which
        contains the number of a grant which supported the work presented in
        the article. Its content allows text, numbers, special characters, and
        various kinds of formatting elements. It's attributes are id, rid, and
        content-type in addition to the xlink: attributes and xmlns: attribute.
        """
        grant_nums = []
        gn = namedtuple('Grant_Num', 'node, id, rid, content_type')
        for gnum in element_methods.get_children_by_tag_name('grant-num', self.article_meta):
            gid = gnum.getAttribute('id')
            grd = gnum.getAttribute('rid')
            gct = gnum.getAttribute('content-type')
            grant_nums.append(gn(gnum, gid, grd, gct))
        return grant_nums

    def get_grant_sponsor(self):
        """
        <grant-sponsor> is an optional element, 0 or more, in <article-meta>
        which contains the name of a grant supplier for the work presented in
        the article. It's content model is like that of <grant-num>.
        """
        grant_sponsors = []
        gs = namedtuple('Grant_Sponsor', 'node, id, rid, content_type')
        for gspo in element_methods.get_children_by_tag_name('grant-sponsor', self.article_meta):
            gid = gspo.getAttribute('id')
            grd = gspo.getAttribute('rid')
            gct = gspo.getAttribute('content-type')
            grant_sponsors.append(gs(gspo, gid, grd, gct))
        return grant_sponsors

    def dtd_version(self):
        return '2.3'


class JPTSMetaData30(JPTSMetaData):
    """
    This is the derived class for version 3.0 of the Journal Publishing Tag Set
    metadata.
    """

    def get_top_floats_group(self):
        """
        <floats-group> may exist as a top level element for DTD v3.0. This
        tag may only exist under <article>, <sub-article>, or <response>.
        This function will only return a <floats-group> node underneath
        <article>, the top level element.
        """
        floats_wrap = self.doc.getElementsByTagName('floats-group')
        for fw in floats_wrap:
            if fw.parentNode.tagName == 'article':
                return fw
        return None

    def parse_journal_metadata(self):
        """
        <journal-meta> stores information about the journal in which
        the article is found.
        """
        jm = self.journal_meta  # More compact
        #There will be one or more <journal-id> elements, which will be indexed
        #in a dictionary by their 'journal-id-type' attributes
        self.journal_id = self.get_journal_id()
        #<journal-title-group> is zero or more and has 'content-type' attribute
        #It contains zero or more of the following:
        #  <journal-title> with 'xml:lang' and 'content-type' attributes
        #  <journal-subtitle> with 'xml:lang' and 'content-type' attributes
        #  <trans-title> with 'xml:lang', 'id', and 'content-type' attributes
        #  <abbrev-journal-title> with 'xml:lang' and 'abbrev-type' attributes
        #The following treatment produces a dictionary keyed by content type
        #whose values are namedtuples containing lists of each element type
        title_groups = jm.getElementsByTagName('journal-title-group')
        tg = namedtuple('Journal_Title_Group', 'title, subtitle, trans, abbrev')
        self.journal_title_group = {}
        for group in title_groups:
            g = []
            for elem in ['journal-title', 'journal-subtitle', 'trans-title',
                         'abbrev-journal-title']:
                g.append(group.getElementsByTagName(elem))
            g = tg(g[0], g[1], g[2], g[3])
            self.journal_title_group[group.getAttribute('content-type')] = g
        #<issn> is one or more and has 'pub-type' attribute
        self.issn = self.get_ISSN()
        #<isbn> is zero or more and has 'content-type' attribute
        self.isbn = {}
        for i in jm.getElementsByTagName('isbn'):
            self.isbn[i.getAttribute('content-type')] = utils.nodeText(i)
        self.publisher = self.get_publisher()  # publisher.loc is a node
        self.jm_notes = self.get_journal_meta_notes()

    def parse_article_metadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        am = self.article_meta  # More compact
        #There will be zero or more <article-id> elements whose text data will
        #by indexed by their pub-id-type attribute values
        self.article_id = self.get_article_id()
        self.article_categories = self.get_article_categories()
        self.title_group = self.get_title_group()
        atg = namedtuple('Article_Title_Group', 'article_title, subtitle, trans_title, trans_subtitle, alt_title, fn_group')
        article = self.title_group.getElementsByTagName('article-title')[0]
        subtitle = self.title_group.getElementsByTagName('subtitle')
        #<trans-title> tags
        trans_title = []
        tt = namedtuple('trans_title', 'Node, content_type, id, xml_lang')
        for e in self.title_group.getElementsByTagName('trans-title'):
            ct = e.getAttribute('content-type')
            eid = e.getAttribute('id')
            xl = e.getAttribute('xml:lang')
            new = tt(e, ct, eid, xl)
            trans_title.append(new)
        #<trans-subtitle> tags
        trans_sub = []
        ts = namedtuple('trans_subtitle', 'Node, content_type, id, xml_lang')
        for e in self.title_group.getElementsByTagName('trans-subtitle'):
            ct = e.getAttribute('content-type')
            eid = e.getAttribute('id')
            xl = e.getAttribute('xml:lang')
            new = ts(e, ct, eid, xl)
            trans_sub.append(new)
        #<alt-title> tags
        alt = {}
        for a in self.title_group.getElementsByTagName('alt-title'):
            alt[a.getAttribute('alt-title-type')] = a
        #<fn-group> tag
        try:
            fn = self.title_group.getElementsByTagName('fn-group')[0]
        except IndexError:
            fn = None
        #Set self.title now
        self.title = atg(article, subtitle, trans_title, trans_sub, alt, fn)
        self.contrib_group = self.get_contrib_group()
        self.contrib = []
        for each in self.contrib_group:
            self.contrib += each.contributors()
        self.affs, self.affs_by_id = self.get_aff()
        self.author_notes = self.get_author_notes()
        self.pub_date = self.get_pub_date()
        self.volume = self.get_volume()
        self.volume_id = self.get_volume_id()
        self.issue = self.get_issue()
        self.issue_id = self.get_issue_id()
        self.supplement = self.get_supplement()
        #Get values for elocation_id, fpage, lpage, and page_range
        self.elocation_id = self.get_elocation_id()
        if self.elocation_id:
            self.fpage = None
            self.lpage = None
            self.page_range = None
        else:
            self.fpage = self.get_fpage()
            self.lpage = self.get_lpage()
            self.page_range = self.get_page_range()
        self.email = self.get_email()
        self.ext_link = self.get_ext_link()
        self.uri = self.get_URI()
        self.product = self.get_product()
        self.supplementary_material = self.get_supplementary_material()
        self.history = self.get_history()
        self.permissions = self.get_permissions()
        self.self_uri = self.get_self_URI()
        self.related_article = self.get_related_article()
        self.abstract = self.get_abstract()
        self.trans_abstract = self.get_trans_abstract()
        self.kwd_group, self.all_kwds, self.all_cmpd_kwds = self.get_kwd_group()
        self.funding_group = self.get_funding_group()
        self.conference = self.get_conference()
        self.counts = self.get_counts()
        self.custom_meta_wrap = self.get_custom_meta_wrap()

    def get_volume(self):
        """
        This method operates on the optional, 0 or 1, element <volume>. Its
        potential attributes, seq and content-type will be extracted.
        """
        volume = namedtuple('Volume', 'value, seq, content_type')
        try:
            vol = element_methods.get_children_by_tag_name('volume', self.article_meta)[0]
        except IndexError:
            return None
        else:
            text = utils.nodeText(vol)
            seq = vol.getAttribute('seq')
            ct = vol.getAttribute('content-type')
            return volume(text, seq, ct)

    def get_kwd_group(self):
        """
        <kwd-group> is an optional element, 0 or more, in <article-meta> which
        may contain 0 or 1 <label> elements, 0 or 1 <title> elements, 1 or more
        of any of <kwd> or <compound-kwd> elements. The content of <kwd>
        elements includes text, numbers, special characters, and emphasis
        elements. Please review the version 3.0 specification for <kwd-group>
        for discussion of this element and explanation for this method's code.
        """
        kwd_groups = []  # There may be more than one
        all_kwds = []  # A list of all keywords
        all_cmpd_kwds = []
        kwd = namedtuple('Keyword', 'node, type, id')
        cmpd_kwd = namedtuple('Compound_Keyword', 'node, type, content_type, id')
        for kg in self.article_meta.getElementsByTagName('kwd-group'):
            kwd_groups.append(kg)
            ktype = kg.getAttribute('keyword-group-type')
            for key in kg.getElementsByTagName('kwd'):
                key_id = key.getAttribute('id')
                all_kwds.append(kwd(key, ktype, key_id))
            for cmpd in kg.getElementsByTagName('compound-kwd'):
                key_id = cmpd.getAttribute('id')
                ct = cmpd.getAttribute('content-type')
                all_cmpd_kwds.append(cmpd_kwd(cmpd, ktype, ct, key_id))
        return kwd_groups, all_kwds, all_cmpd_kwds

    def get_issue(self):
        """
        This method operates on the optional, 0 or 1, element <issue>. Its
        potential attributes, seq and content-type will be extracted.
        """
        issue = namedtuple('Issue', 'value, seq, content_type')
        try:
            iss = element_methods.get_children_by_tag_name('issue', self.article_meta)[0]
        except IndexError:
            return None
        else:
            text = utils.nodeText(iss)
            seq = iss.getAttribute('seq')
            ct = iss.getAttribute('content-type')
            return issue(text, seq, ct)

    def get_funding_group(self):
        """
        <funding-group> is an optional element, 0 or more, in <article-meta>.
        This element takes the functional place of several elements in the
        previous versions of the DTD. This element may show significant
        variation in content, for this reason this method will take the
        simplistic approach of exposing the following sub-elements:

        <award-group>       : 0 or more | award_group - NodeList
        <funding-statement> : 0 or more | funding_statement - NodeList
        <open-access>       : 0 or one  | open_access - Node

        As <funding-group> may appear more than once, this will be a list
        itself.
        """
        funding_tuple = namedtuple('Funding_Group', 'award_group, funding_statement, open_access')
        funding_groups = []
        for funding_group in element_methods.get_children_by_tag_name('funding-group', self.article_meta):
            award_groups = element_methods.get_children_by_tag_name('award-group', funding_group)
            funding_statements = element_methods.get_children_by_tag_name('funding-statement', funding_group)
            open_access = element_methods.get_children_by_tag_name('open-access', funding_group)
            if open_access:
                open_access = open_access[0]
            new = funding_tuple(award_groups, funding_statements, open_access)
            funding_groups.append(new)
        return funding_groups

    def parse_back_data(self):
        """
        The JPTS 3.0 defines the following as back elements, which <back>
        may have any combination of:

        <ack> Acknowledgments
        <app-group> Appendix Matter
        <bio> Biography
        <fn-group> Footnote Group
        <glossary> Glossary Elements List
        <ref-list> Reference List (Bibliographic Reference List)
        <notes> Notes
        <sec> Section

        All of these will be NodeLists in the self.backmatter namedtuple.
        """
        #No point in looking for back matter if no back element
        if not self.back:
            self.backmatter = None
            return

        #Define the namedtuple for backmatter
        back_tuple = namedtuple('Back_Matter',
                                'ack, app_group, bio, fn_group, glossary, ref_list, notes, sec')

        #Populate backmatter
        nodes = []
        for node_name in ['ack', 'app-group', 'bio', 'fn-group', 'glossary',
                          'ref-list', 'notes', 'sec']:
            nodes.append(element_methods.get_children_by_tag_name(node_name, self.back))
        self.backmatter = back_tuple(*nodes)

    def dtd_version(self):
        return '3.0'
