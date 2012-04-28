"""
This module contains classes representing metadata in the Journal Publishing
Tag Set. There is a base class providing a baseline of functionality for the
JPTS and derived classes for distinct version of the Tag Set. With this
implementation, the commonalities between versions may be presented in the base
class while their differences may be presented in their derived classes. An
important distinction is to be made between publisher and the DTD version; for
full extensibility in development, they are unique parameters. As a class for
metadata, this class will handle everything except <body>
"""

import utils
import collections


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
        vary between version, this class will be overriddeby the derived
        classes. <journal-meta> stores information about the journal in which
        the article is found.
        """
        return None
    
    def parseArticleMetadata(self):
        """
        As the specifications for metadata under the <article-meta> element
        vary between version, this class will be overriddeby the derived
        classes. <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        return None
    
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
        self.journal_id = {}
        for j in jm.getElementsByTagName('journal-id'):
            text = utils.nodeText(j)
            self.journal_id[j.getAttribute('journal-id-type')] = text
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
        self.issn = {}
        for i in jm.getElementsByTagName('issn'):
            self.issn[i.getAttribute('pub-type')] = utils.nodeText(i)
        #<publisher> is zero or one; If it exists, it will contain:
        #one <publisher-name> and zero or one <publisher-loc>
        if jm.getElementsByTagName('publisher'):
            self.publisher_name = jm.getElementsByTagName('publisher-name')[0]
            self.publisher_name = utils.nodeText(self.publisher_name)
            ploc = jm.getElementsByTagName('publisher-loc')
            if ploc:
                self.publisher_loc = utils.nodeText(ploc[0])
        else:
            self.publisher_name = None
            self.publisher_loc = None
        #<notes> is zero or one and has attributes: 'id', and 'notes-type'
        try:
            self.jm_notes = jm.getElementsByTagName('notes')[0]
        except IndexError:
            self.jm_notes = None
    
    def parseArticleMetadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        return None
    
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
        self.journal_id = {}
        for j in jm.getElementsByTagName('journal-id'):
            text = utils.nodeText(j)
            self.journal_id[j.getAttribute('journal-id-type')] = text
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
        self.issn = {}
        for i in jm.getElementsByTagName('issn'):
            self.issn[i.getAttribute('pub-type')] = utils.nodeText(i)
        #<publisher> is zero or one; it has 'content-type' attribute
        #If it exists, it will contain: one <publisher-name> and zero or one 
        #<publisher-loc>
        publisher = jm.getElementsByTagName('publisher')
        if publisher:
            self.pub_content_type = publisher[0].getAttribute('content-type')
            self.publisher_name = jm.getElementsByTagName('publisher-name')[0]
            self.publisher_name = utils.nodeText(self.publisher_name)
            #Publisher location may contain <email>, <ext-link>, and <uri> in
            #addition to text, numbers, and special characters
            try:
                ploc = jm.getElementsByTagName('publisher-loc')[0]
            except IndexError:
                self.publisher_loc = None
        else:
            self.publisher_name = None
            self.publisher_loc = None
        #<notes> is zero or one and has attributes: 'id', and 'notes-type'
        try:
            self.jm_notes = jm.getElementsByTagName('notes')[0]
        except IndexError:
            self.jm_notes = None
    
    def parseArticleMetadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        return None
    
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
        This function will only return a <floats-group> node underneath article,
        the top level element.
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
        self.journal_id = {}
        for j in jm.getElementsByTagName('journal-id'):
            text = utils.nodeText(j)
            self.journal_id[j.getAttribute('journal-id-type')] = text
        #<journal-title-group> is zero or more and has 'content-type' attribute
        #It contains zero or more of the following:
        #  <journal-title> with 'xml:lang' and 'content-type' attributes
        #  <journal-subtitle> with 'xml:lang' and 'content-type' attributes
        #  <trans-title> with 'xml:lang', 'id', and 'content-type' attributes
        #  <abbrev-journal-title> with 'xml:lang' and 'abbrev-type' attributes
        #The following treatment produces a dictionary keyed by content type
        #whose values are namedtuples containing lists of each element type
        title_groups = jm.getElementsByTagName('journal-title-group')
        tg = collections.namedtuple('Journal_Title_Group', 'title, subtitle, \
trans, abbrev')
        self.journal_title_group = {}
        for group in title_groups:
            g = []
            for elem in ['journal-title', 'journal-subtitle', 'trans-title',
                         'abbrev-journal-title']:
                g.append(group.getElementsByTagName(elem))
            g = tg(g[0], g[1], g[2], g[3])
            self.journal_title_group[group.getAttribute('content-type')] = g
        #<issn> is one or more and has 'pub-type' attribute
        self.issn = {}
        for i in jm.getElementsByTagName('issn'):
            self.issn[i.getAttribute('pub-type')] = utils.nodeText(i)
        #<isbn> is zero or more and has 'content-type' attribute
        self.isbn = {}
        for i in jm.getElementsByTagName('isbn'):
            self.isbn[i.getAttribute('content-type')] = utils.nodeText(i)
        #<publisher> is zero or one; it has 'content-type' attribute
        #If it exists, it will contain: one <publisher-name> and zero or one 
        #<publisher-loc>
        publisher = jm.getElementsByTagName('publisher')
        if publisher:
            self.pub_content_type = publisher[0].getAttribute('content-type')
            self.publisher_name = jm.getElementsByTagName('publisher-name')[0]
            self.publisher_name = utils.nodeText(self.publisher_name)
            #Publisher location may contain <email>, <ext-link>, and <uri> in
            #addition to text, numbers, and special characters
            try:
                ploc = jm.getElementsByTagName('publisher-loc')[0]
            except IndexError:
                self.publisher_loc = None
        else:
            self.publisher_name = None
            self.publisher_loc = None
        #<notes> is zero or one and has attributes: 'id', and 'notes-type'
        try:
            self.jm_notes = jm.getElementsByTagName('notes')[0]
        except IndexError:
            self.jm_notes = None
    
    def parseArticleMetadata(self):
        """
        <article-meta> stores information about the article and the
        issue of the journal in which it is found.
        """
        return None
    
    def dtdVersion(self): 
        return '3.0'
