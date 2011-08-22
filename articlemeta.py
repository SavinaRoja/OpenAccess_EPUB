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
        self.author_summary = None
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
                    self.author_summary = entry
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
        for pd in pub_dates:
            day = 0
            month = getTagData(pd.getElementsByTagName('month'))
            year = getTagData(pd.getElementsByTagName('year'))
            if pd.getAttribute('pub-type') == u'collection':
                self.art_dates['collection'] = [day, month, year]
            elif pd.getAttribute('pub-type') == u'epub':
                day = getTagData(pd.getElementsByTagName('day'))
                self.art_dates['epub'] = [day, month, year]
        
class ArticleCategories(object):
    """Article Categories information"""
    def __init__(self, node):
        self.series_text = u''
        self.series_title = []
        self.subj_groups = None
        self.identify(node)

    def identify(self, node):
        """pull everything from the xml node"""
        self.series_text = getTagData(node.getElementsByTagName('series-text'))
        tmp = node.getElementsByTagName('series-title')
        for item in tmp:
            title = item.firstChild.data
            self.series_title.append(title)
        self.subj_groups = node.getElementsByTagName('subj-group')