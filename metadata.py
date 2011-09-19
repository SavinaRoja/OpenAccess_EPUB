"""Handles metadata related tasks for the article"""
import logging
from utils import getTagData

class FrontMatter(object):
    """Article metadata"""
    def __init__(self, front):
        
        #The front node may contain <journal-meta>,<article-meta>,<notes>
        journal_metanode = front.getElementsByTagName('journal-meta')[0]
        article_metanode = front.getElementsByTagName('article-meta')[0]
        notesnodes = front.getElementsByTagName('notes')
        
        #Create a JournalMeta object as attribute
        self.journal_meta = JournalMeta(journal_metanode)
        logging.debug(self.journal_meta)
                
        #Create an ArticleMeta object as attribute
        self.article_meta = ArticleMeta(article_metanode)
        logging.debug(self.article_meta)
        
        #Notes generally do not contain data critical to rendering the 
        #document at hand. For the time being, notes will be kept in the list
        self.notes = notesnodes
        
        logging.debug('FrontMatter init complete')
        logging.debug(self)
            
    def __str__(self):
        retstr = 'FrontMatter'
        return retstr
    
"""Article metadata"""
import epub_date
from utils import Identifier, getTagData
import logging
import contributor, crossrefs

class ArticleMeta(object):
    """Article metadata"""
    def __init__(self, node):
        self.identifiers = set()
        self.article_categories = None 
        self.title = None
        self.alt_title = None
        self.trans_title = None
        self.subtitle = None
        self.title_fn = None 
        self.publication_dates = None
        self.volume = None
        self.issue = None
        self.issue_id = None
        self.issue_title = None
        # object for copyright-statement AND copyright-year
        self.copyright = None
        
        self.history = {}
        self.abstract = None
        self.summary = None
        self.art_auths = [] # A list of authors.
        self.art_edits = [] # A list of editors.
        self.art_other_contrib = [] # unclassified contributors
        self.art_affs = []
        self.art_corresps = []
        self.art_dates = {}
        self.art_auth_contribs = None
        self.art_copyright_year = None
        self.art_copyright_statement = None
        self.art_eloc_id = None
        self.related_articles = []
        
        self.identify(node)
        
    def identify(self, node):
        """pull everything from the xml node"""
        # get article-id nodes
        id_nodes = node.getElementsByTagName('article-id')
        for item in id_nodes:
            id_data = item.firstChild.data
            id_type = item.getAttribute('pub-id-type')
            ident = Identifier(id_data, id_type)
            logging.debug(ident)
            self.identifiers.add(ident)
            
        # history
        hist = node.getElementsByTagName('history')[0]
        dates = hist.getElementsByTagName('date')
        for entry in dates:
            entry_date = epub_date.DateInfo(entry)
            self.history[entry.getAttribute('date-type')] = entry_date
        
        # title and alternate title
        title_grps = node.getElementsByTagName('title-group')
        for title_grp in title_grps:
            self.title = getTagData(title_grp.getElementsByTagName('article-title'))
            self.alt_title = getTagData(title_grp.getElementsByTagName('alt-title'))
            self.trans_title = getTagData(title_grp.getElementsByTagName('trans-title'))
            self.subtitle = getTagData(title_grp.getElementsByTagName('subtitle'))
        
        self.volume = getTagData(node.getElementsByTagName('volume'))
        
        # Abstract nodes become attributes
        abstracts = node.getElementsByTagName('abstract')
        for entry in abstracts:
            if not entry.hasAttributes():
                self.abstract = entry
            else:
                if entry.getAttribute('abstract-type') == 'summary':
                    self.summary = entry
                else:
                    print('unknown abstract type')
        
        # Article categories
        tmp = node.getElementsByTagName('article-categories')[0]
        self.article_categories = ArticleCategories(tmp)
        
        # Issue: <issue> number, <issue-id> identifier, <issue-title> title
        self.issue = getTagData(node.getElementsByTagName('issue'))
        self.issue_id = getTagData(node.getElementsByTagName('issue-id'))
        self.issue_title = getTagData(node.getElementsByTagName('issue-title'))
        
        contrib_groups = node.getElementsByTagName('contrib-group')
        contributor_list = []
        for group in contrib_groups:
            contribs = group.getElementsByTagName('contrib')
            for contrib in contribs:
                contributor_list.append(contrib)
        
        for contrib in contributor_list:
            if contrib.getAttribute('contrib-type') == u'author':
                self.art_auths.append(contributor.Author(contrib))
            elif contrib.getAttribute('contrib-type') == u'editor':
                self.art_edits.append(contributor.Editor(contrib))
            else:
                self.art_other_contrib.append(contributor.Contributor(contrib))

        affs = node.getElementsByTagName('aff')
        for aff in affs:
            self.art_affs.append(crossrefs.Affiliation(aff))
        
        author_notes = node.getElementsByTagName('author-notes')[0]
        correspondences = author_notes.getElementsByTagName('corresp')
        
        for corr in correspondences:
            self.art_corresps.append(crossrefs.Correspondence(corr))
        
        auth_notes_fn = author_notes.getElementsByTagName('fn')[0]
        auth_notes_fn_p = auth_notes_fn.getElementsByTagName('p')[0]
        
        self.art_auth_contribs = auth_notes_fn_p.firstChild.data
        copyright_year = node.getElementsByTagName('copyright-year')[0]
        self.art_copyright_year = copyright_year.firstChild.data
        cpright = node.getElementsByTagName('copyright-statement')[0]
        self.art_copyright_statement = cpright.firstChild.data
        elocation_id = node.getElementsByTagName('elocation-id')[0]
        self.art_eloc_id = elocation_id.firstChild.data
        
        pub_dates = node.getElementsByTagName('pub-date')
        for entry in pub_dates:
            entry_date = epub_date.DateInfo(entry)
            self.art_dates[entry.getAttribute('pub-type')] = entry_date
        
class ArticleCategories(object):
    """Article Categories information"""
    def __init__(self, node):
        self.series_text = u''
        self.series_title = []
        self.subj_groups = {}
        self.identify(node)

    def identify(self, node):
        """pull everything from the xml node"""
        self.series_text = getTagData(node.getElementsByTagName('series-text'))
        tmp = node.getElementsByTagName('series-title')
        for item in tmp:
            title = item.firstChild.data
            self.series_title.append(title)
        subj_group_nodes = node.getElementsByTagName('subj-group')
        for each in subj_group_nodes:
            type = each.getAttribute('subj-group-type')
            subj_list = []
            subj_nodes = each.getElementsByTagName('subject')
            for subj_node in subj_nodes:
                subj_list.append(getTagData([subj_node]))
            self.subj_groups[type] = subj_list
            
        
class JournalMeta(object):
    '''
    Journal-level metadata
    journal_meta_node -- XML node containing journal metadata
    '''
    def __init__(self, journal_meta_node):
        self.source = journal_meta_node
        self.identifier = {}
        self.title = []
        self.title_abbr = []
        self.issn = {}
        self.publisher = None
        self.notes = None
        self.identify(journal_meta_node)
        self.notes_status = False
    
    def identify(self, journal_meta_node):
        '''process metadata'''
        # Collect a list of all journal-title nodes
        journal_title = journal_meta_node.getElementsByTagName('journal-title')
        
        # Extract title strings from journal-title nodes into self.title list
        for jrn_tit in journal_title:
            self.title.append(jrn_tit.firstChild.data)
        
        # Collect a list of all abbrev-journal-title nodes
        abbr_titles = 'abbrev-journal-title'
        abbrev_titles = journal_meta_node.getElementsByTagName(abbr_titles)
        
        # Extract abbreviated title strings
        for abbr_jrn_tit in abbrev_titles:
            self.title_abbr.append(abbr_jrn_tit.firstChild.data)

        # Collect a list of all ISSN nodes
        issns = journal_meta_node.getElementsByTagName('issn')

        # enter ISSNs into self.issn with associated pub-type strings
        for item in issns:
            issn_id = item.firstChild.data
            self.issn[issn_id] = item.getAttribute('pub-type')
            
        # Collect a list of all journal-id nodes
        journal_id = journal_meta_node.getElementsByTagName('journal-id')
        
        # enter journal-ids into self.identifier with associated
        # journal-id-type strings
        for jid in journal_id:
            jrn_id_type = jid.getAttribute('journal-id-type')
            self.identifier[jrn_id_type] = jid.firstChild.data

        # Create a notes node, if such exists
        notes = journal_meta_node.getElementsByTagName('notes')
        if notes:
            self.notes_status = True
                
        # Collect the publisher node
        publisher_node = journal_meta_node.getElementsByTagName('publisher')[0]
        
        # Instantiate an instance of Publisher(node)
        self.publisher = Publisher(publisher_node)
        
    def __str__(self):
        tmpstr = 'Journal Title(s):{0} |Abbreviated Title(s):{1} |Journal IDs:'
        tmpstr = tmpstr + '{2}|ISSNs: {3} |Notes?: {4} |Publisher: {5}'
        titlestr = u''
        for title in self.title:
            titlestr = titlestr + ' ' + title
            
        abbrtitlestr = u''
        for abbrtitle in self.title_abbr:
            abbrtitlestr = abbrtitlestr + '' + abbrtitle
        
        jidstr = u''
        for key, value in self.identifier.iteritems():
            jidstr = jidstr + key + '; ' + value + ', '

        issnstr = u''
        for key, value in self.issn.iteritems():
            issnstr = issnstr + key + '; ' + value + ', '
        
        pubstr = self.publisher.__str__()
        outstr = tmpstr.format(titlestr,
                               abbrtitlestr,
                               jidstr,
                               issnstr,
                               self.notes_status,
                               pubstr)
        return outstr

class Publisher(object):
    '''
    Publisher information
    node -- publisher node from an XML document object
    '''
    def __init__(self, publisher_node):
        self.name = u''
        self.location = u''
        self.identify(publisher_node)
    
    def identify(self, publisher_node):
        '''Pulls info from the xml'''
        tmp = publisher_node.getElementsByTagName('publisher-name')[0]
        self.name = tmp.firstChild.data
        tmp = publisher_node.getElementsByTagName('publisher-loc')[0]
        self.location = tmp.firstChild.data
        
    def __str__(self):
        pubstring = 'Publisher Name: {0}, Publisher Location: {1}'
        retstr = pubstring.format(self.name, self.location)
        return retstr