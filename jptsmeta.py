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

import utils
import collections
import jptscontrib


class JPTSMeta(object):
    """
    This is the base class for the Journal Publishing Tag Set metadata.
    """
    def __init__(self, document, publisher):
        self.doc = document
        self.publisher = publisher
        self.getTopElements()
        self.getFrontElements()
        self.parseJournalMetadata()
        self.parseArticleMetadata()

    def getTopElements(self):
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
        self.floats_wrap = self.getTopFloats_Wrap()  # relevant to v2.3
        self.floats_group = self.getTopFloats_Group()  # relevant to v3.0

    def getTopFloats_Wrap(self):
        return None

    def getTopFloats_Group(self):
        return None

    def getFrontElements(self):
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

    def parseJournalMetadata(self):
        """
        As the specifications for metadata under the <journal-meta> element
        vary between version, this class will be overridden by the derived
        classes. <journal-meta> stores information about the journal in which
        the article is found.
        """
        return None

    def getJournalID(self):
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

    def getISSN(self):
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

    def getPublisher(self):
        """
        <publisher> under <journal-meta> is an optional tag, zero or one, which
        under some DTD versions has the attribute 'content-type'. If it exists,
        it contains one <publisher-name> element which contains only text,
        numbers, or special characters. It also may include one <publisher-loc>
        element which has text, numbers, special characters, and the address
        linking elements <email>, <ext-link>, and <uri>. This function returns
        the publisher information as a namedtuple for simple access.
        """
        pd = collections.namedtuple('Publisher', 'name, loc, content_type')
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

    def getJournalMetaNotes(self):
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

    def parseArticleMetadata(self):
        """
        As the specifications for metadata under the <article-meta> element
        vary between version, this class will be overridden by the derived
        classes. <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        return None

    def getArticleID(self):
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

    def getArticleCategories(self):
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

    def getTitleGroup(self):
        """
        <title-group> is a required element underneath the <article-meta> tag.
        Below this level, each specification has its own way of constructing
        its title elements.
        """
        return self.article_meta.getElementsByTagName('title-group')[0]

    def getContribGroup(self):
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

    def getAff(self):
        """
        <aff> is an optional tag that can be contained in <article-meta>,
        <collab>, <contrib>, <contrib-group>, <person-group>, and (in the case
        of v2.3 and v3.0) <front-stub>. It's potential attributes are id, rid,
        and content-type. It is commonly referred to by other elements, thus it
        is important to make its attributes accessible. It's contents are
        diverse, but they include the address elements which may feature
        heavily.
        """
        affs = self.getChildrenByTagName('aff', self.article_meta)
        affsbyid = {}
        for aff in affs:
            aid = aff.getAttribute('id')
            affsbyid[aid] = aff
        return affs, affsbyid

    def getAuthorNotes(self):
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

    def getPubDate(self):
        """
        <pub-date> is a mandatory element, 1 or more, within the <article-meta>
        element. It has a single attribute, pub-type, and its content model is:
        (((day?, month?) | season)?, year)
        This is common between DTD versions. This method returns a dictionary
        of namedtuples whose keys are the values of the pub-type attribute.
        """
        pd = collections.namedtuple('Pub_Date', 'Node, year, month, day, season, pub_type')
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

    def getChildrenByTagName(self, searchterm, node):
        """
        This method differs from getElementsByTagName() by only searching the
        childNodes of the specified node. The node must also be specified along
        with the searchterm.
        """
        nodelist = []
        for c in node.childNodes:
            try:
                tag = c.tagName
            except AttributeError:  # Text nodes have no tagName
                pass
            else:
                if tag == searchterm:
                    nodelist.append(c)
        return nodelist

    def dtdVersion(self):
        return None


class JPTSMeta20(JPTSMeta):
    """
    This is the derived class for version 2.0 of the Journal Publishing Tag Set
    metadata.
    """

    def parseJournalMetadata(self):
        """
        <journal-meta> stores information about the journal in which
        the article is found.
        """
        jm = self.journal_meta  # More compact
        #There will be one or more <journal-id> elements, which will be indexed
        #in a dictionary by their 'journal-id-type' attributes
        self.journal_id = self.getJournalID()
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
        self.issn = self.getISSN()
        self.publisher = self.getPublisher()  # publisher.loc is text
        self.jm_notes = self.getJournalMetaNotes()

    def parseArticleMetadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        am = self.article_meta  # More compact
        #There will be zero or more <article-id> elements whose text data will
        #by indexed by their pub-id-type attribute values
        self.article_id = self.getArticleID()
        self.article_categories = self.getArticleCategories()
        self.title_group = self.getTitleGroup()
        #self.title will be a namedtuple comprised of the elements under
        #<title-group>. names will be set by their elements, and values will
        #be set by the following types
        #article_title : Node
        #subtitle      : NodeList
        #trans-title   : dictionary[xml:lang]
        #alt-title     : dictionary[alt-title-type]
        #fn_group      : Node
        atg = collections.namedtuple('Article_Title_Group', 'article_title, subtitle, trans_title, alt_title, fn_group')
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
        self.contrib_group = self.getContribGroup()
        self.contrib = []
        for each in self.contrib_group:
            self.contrib += each.contributors()
        self.affs, self.affs_by_id = self.getAff()
        self.author_notes = self.getAuthorNotes()
        self.pub_date = self.getPubDate()

    def dtdVersion(self):
        return '2.0'


class JPTSMeta23(JPTSMeta):
    """
    This is the derived class for version 2.3 of the Journal Publishing Tag Set
    metadata.
    """

    def getTopFloats_Wrap(self):
        """
        <floats-wrap> may exist as a top level element for DTD v2.3. This
        tag may only exist under <article>, <sub-article>, or <response>.
        This function will only return a <floats-wrap> node underneath article,
        the top level element.
        """
        floats_wrap = self.doc.getElementsByTagName('floats-wrap')
        for fw in floats_wrap:
            if fw.parentNode.tagName == u'article':
                return fw
        return None

    def parseJournalMetadata(self):
        """
        <journal-meta> stores information about the journal in which
        the article is found.
        """
        jm = self.journal_meta  # More compact
        #There will be one or more <journal-id> elements, which will be indexed
        #in a dictionary by their 'journal-id-type' attributes
        self.journal_id = self.getJournalID()
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
        self.issn = self.getISSN()
        self.publisher = self.getPublisher()  # publisher.loc is a node
        self.jm_notes = self.getJournalMetaNotes()

    def parseArticleMetadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        am = self.article_meta  # More compact
        #There will be zero or more <article-id> elements whose text data will
        #by indexed by their pub-id-type attribute values
        self.article_id = self.getArticleID()
        self.article_categories = self.getArticleCategories()
        self.title_group = self.getTitleGroup()
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
        atg = collections.namedtuple('Article_Title_Group', 'article_title, subtitle, trans_title, trans_subtitle, alt_title, fn_group')
        article = self.title_group.getElementsByTagName('article-title')[0]
        subtitle = self.title_group.getElementsByTagName('subtitle')
        #<trans-title> tags
        trans_title = []
        tt = collections.namedtuple('trans_title', 'Node, content_type, id, xml_lang')
        for e in self.title_group.getElementsByTagName('trans-title'):
            ct = e.getAttribute('content-type')
            eid = e.getAttribute('id')
            xl = e.getAttribute('xml:lang')
            new = tt(e, ct, eid, xl)
            trans_title.append(new)
        #<trans-subtitle> tags
        trans_sub = []
        ts = collections.namedtuple('trans_subtitle', 'Node, content_type, id, xml_lang')
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
        self.contrib_group = self.getContribGroup()
        self.contrib = []
        for each in self.contrib_group:
            self.contrib += each.contributors()
        self.affs, self.affs_by_id = self.getAff()
        self.author_notes = self.getAuthorNotes()
        self.pub_date = self.getPubDate()

    def dtdVersion(self):
        return '2.3'


class JPTSMeta30(JPTSMeta):
    """
    This is the derived class for version 3.0 of the Journal Publishing Tag Set
    metadata.
    """

    def getTopFloats_Group(self):
        """
        <floats-group> may exist as a top level element for DTD v3.0. This
        tag may only exist under <article>, <sub-article>, or <response>.
        This function will only return a <floats-group> node underneath
        <article>, the top level element.
        """
        floats_wrap = self.doc.getElementsByTagName('floats-group')
        for fw in floats_wrap:
            if fw.parentNode.tagName == u'article':
                return fw
        return None

    def parseJournalMetadata(self):
        """
        <journal-meta> stores information about the journal in which
        the article is found.
        """
        jm = self.journal_meta  # More compact
        #There will be one or more <journal-id> elements, which will be indexed
        #in a dictionary by their 'journal-id-type' attributes
        self.journal_id = self.getJournalID()
        #<journal-title-group> is zero or more and has 'content-type' attribute
        #It contains zero or more of the following:
        #  <journal-title> with 'xml:lang' and 'content-type' attributes
        #  <journal-subtitle> with 'xml:lang' and 'content-type' attributes
        #  <trans-title> with 'xml:lang', 'id', and 'content-type' attributes
        #  <abbrev-journal-title> with 'xml:lang' and 'abbrev-type' attributes
        #The following treatment produces a dictionary keyed by content type
        #whose values are namedtuples containing lists of each element type
        title_groups = jm.getElementsByTagName('journal-title-group')
        tg = collections.namedtuple('Journal_Title_Group', 'title, subtitle, trans, abbrev')
        self.journal_title_group = {}
        for group in title_groups:
            g = []
            for elem in ['journal-title', 'journal-subtitle', 'trans-title',
                         'abbrev-journal-title']:
                g.append(group.getElementsByTagName(elem))
            g = tg(g[0], g[1], g[2], g[3])
            self.journal_title_group[group.getAttribute('content-type')] = g
        #<issn> is one or more and has 'pub-type' attribute
        self.issn = self.getISSN()
        #<isbn> is zero or more and has 'content-type' attribute
        self.isbn = {}
        for i in jm.getElementsByTagName('isbn'):
            self.isbn[i.getAttribute('content-type')] = utils.nodeText(i)
        self.publisher = self.getPublisher()  # publisher.loc is a node
        self.jm_notes = self.getJournalMetaNotes()

    def parseArticleMetadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        am = self.article_meta  # More compact
        #There will be zero or more <article-id> elements whose text data will
        #by indexed by their pub-id-type attribute values
        self.article_id = self.getArticleID()
        self.article_categories = self.getArticleCategories()
        self.title_group = self.getTitleGroup()
        atg = collections.namedtuple('Article_Title_Group', 'article_title, subtitle, trans_title, trans_subtitle, alt_title, fn_group')
        article = self.title_group.getElementsByTagName('article-title')[0]
        subtitle = self.title_group.getElementsByTagName('subtitle')
        #<trans-title> tags
        trans_title = []
        tt = collections.namedtuple('trans_title', 'Node, content_type, id, xml_lang')
        for e in self.title_group.getElementsByTagName('trans-title'):
            ct = e.getAttribute('content-type')
            eid = e.getAttribute('id')
            xl = e.getAttribute('xml:lang')
            new = tt(e, ct, eid, xl)
            trans_title.append(new)
        #<trans-subtitle> tags
        trans_sub = []
        ts = collections.namedtuple('trans_subtitle', 'Node, content_type, id, xml_lang')
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
        self.contrib_group = self.getContribGroup()
        self.contrib = []
        for each in self.contrib_group:
            self.contrib += each.contributors()
        self.affs, self.affs_by_id = self.getAff()
        self.author_notes = self.getAuthorNotes()
        self.pub_date = self.getPubDate()

    def dtdVersion(self):
        return '3.0'
