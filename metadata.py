"""Handles metadata related tasks for the article"""
import logging
import epub_date
import contributor, crossrefs
import xml.dom
from utils import *

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

class ArticleMeta(object):
    '''Article Metadata: this class takes the <article-meta> element as input 
    and holds representations of the data its children contain as local 
    attributes. The specification for the <article-meta> tag can be found at: 
    http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-p5c0.html'''
    
    #The elements contained in the article-meta may exist under certain defined
    #conditions: zero or one, zero or more, one of (options)...
    #For the sake of clarity and consistency, it is wise to apply a similar 
    #approach in the collection of elements with the same condition.
    
    #For "zero or one": collect at most one, or nothing
    #try:
    #    self.article_categories = node.getElementsByTagName('article-categories')[0]
    #except IndexError:
    #    self.article_categories = None
    
    #For "zero or more": collect all of them
    #self.article_id = node.getElementsByTagName('article-id')
    #This is a NodeList of unknown length, iteration over it with a for-loop
    #is possible to act on each Node, or if empty it will evaluate false in an 
    #if-statement.
    
    def __init__(self, node):
        self.identifiers = set()
        self.article_categories = None 
        self.article_title = None
        self.alt_titles = {}
        self.trans_titles = {}
        self.subtitles = []
        self.title_fn = None 
        self.publication_dates = None
        self.volume = None
        self.issue = None
        self.issue_id = None
        self.issue_title = None
        # object for copyright-statement AND copyright-year
        self.copyright = None
        
        self.history = {}
        self.abstracts = {}
        self.summary = None
        self.art_auths = [] # A list of authors.
        self.art_edits = [] # A list of editors.
        self.art_other_contrib = [] # unclassified contributors
        self.art_affs = []
        self.correspondences = None
        self.art_corresps = []
        self.art_dates = {}
        self.art_auth_contribs = None
        self.art_copyright_year = None
        self.art_copyright_statement = None
        self.art_eloc_id = None
        self.related_articles = []
        
        self.identify(node)
        
    def makeIdentifiers(self, nodelist):
        '''This method takes a NodeList of article-id elements and returns a 
        set of "Identifier" namedtuples.'''
        
        id_set = set()
        for article_id in nodelist:
            pub_id_type = article_id.getAttribute('pub-id-type')
            data = getTagText(article_id)
            ident = Identifier(data, pub_id_type)
            logging.debug(ident)
            id_set.add(ident)
        return(id_set)
    
    def makeTitles(self, node):
        '''This method takes a title-group node as input and returns four 
        units of data corresponding to four tags inside the title-group. 
        article-title is returned as a formatted Node, subtitle is returned as 
        a plain NodeList, trans-title is returned as a dictionary mapping 
        values of xml:lang to the Node, and alt-title is returned as a 
        dictionary mapping values of alt-title-type to the Node.'''
        #The article title is a required element, we will return a more nicely 
        #formatted version of it to the self.article_title attribute
        article_title_node = node.getElementsByTagName('article-title')[0]
        article_title = getFormattedNode(article_title_node)
        #Zero or more subtitle nodes, these are rare and have no attributes:
        #Collect a NodeList of them, no planned usage for now
        subtitles = node.getElementsByTagName('subtitle')
        #Zero or more trans-title nodes, these can be distinguished by the 
        #xml:lang attribute, make a dictionary, keying language to node
        trans_titles = node.getElementsByTagName('trans-title')
        trans_title_dict = {}
        for trans_title in trans_titles:
            lang = trans_title.getAttribute('xml:lang')
            title = getFormattedNode(trans_title)
            trans_title_dict[lang] = title
        #Zero or more alt-title nodes, these can be distinguished by the 
        #alt-title-type attribute. make a dictionary, keyed to this attribute
        alt_titles = node.getElementsByTagName('alt-title')
        alt_title_dict = {}
        for alt_title in alt_titles:
            type =alt_title.getAttribute('alt-title-type')
            title = getFormattedNode(alt_title)
            alt_title_dict[type] = title
        #We will ignore the fn-group element for now
        
        return(article_title, subtitles, trans_title_dict, alt_title_dict)
    
    def makeHistory(self, node):
        '''This method takes the <history> node as input and returns a 
        dictionary mapping of dates (epub_date.DateInfo) to the values of the 
        date-type attribute.'''
        dict = {}
        dates = node.getElementsByTagName('date')
        for date in dates:
            date_info = epub_date.DateInfo(date)
            date_type = date.getAttribute('date-type')
            dict[date_type] = date_info
        return(dict)
    
    def identify(self, node):
        """pull everything from the xml node"""
        # get article-id nodes, assign as class attribute for direct accession
        self.article_ids = node.getElementsByTagName('article-id')
        # Create self.identifiers from article-id nodes
        self.identifiers = self.makeIdentifiers(self.article_ids)
        # get article-categories node
        try:
            article_categories_node = node.getElementsByTagName('article-categories')[0]
        except IndexError:
            logging.debug('No article-categories node found')
            self.article_categories = None
        else: #Instantiate ArticleCategories if the node was found
            self.article_categories = ArticleCategories(article_categories_node)
        # get title-group node
        try:
            title_group_node = node.getElementsByTagName('title-group')[0]
        except IndexError:
            logging.critical('title-group not found! Articles need titles!')
        else: #Set the title values with makeTitles()
            self.article_title, self.subtitles, self.trans_titles, self.alt_titles = self.makeTitles(title_group_node)
            
        # history
        try:
            history_node = node.getElementsByTagName('history')[0]
        except IndexError:
            self.history = {}
        else:
            self.history = self.makeHistory(history_node)
        
        self.volume = getTagData(node.getElementsByTagName('volume'))
        
        # Abstract nodes
        for abstract in node.getElementsByTagName('abstract'):
            type = abstract.getAttribute('abstract-type')
            if type:
                self.abstracts[type] = abstract
            else:
                self.abstracts['default'] = abstract
        
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
        self.correspondences = author_notes.getElementsByTagName('corresp')
        
        for corr in self.correspondences:
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
    '''A class representing the <article-categories> in the Journal Publishing 
    Tag Set 2.0'''
    def __init__(self, node):
        self.series_text = u'' #zero or one. Content: text with emphasis
        self.series_titles = [] #zero or more. Content: text with emphasis
        self.subj_groups = {} #zero or more. Content: subject
        self.identify(node)

    def identify(self, node):
        '''Acquire xml elements'''
        #Get the series-text node which can include emphasis elements
        try:
            series_text_node = node.getElementsByTagName('series-text')[0]
        except IndexError:
            pass
        else:
            self.series_text = getFormattedNode(series_text_node)
            
        #Get the series-title nodes which may contain emphasis elements
        series_title_nodes = node.getElementsByTagName('series-title')
        for item in series_title_nodes:
            self.series_titles.append(getFormattedNode(item))
            
        #Subj-groups can be simple or complicated, specific to individual 
        #practice by publisher. PLoS appears to keep it simple, and uses either
        #subj-group-type = "Discipline" or "Discipline-v2" These subject nodes 
        #will be assigned to lists according to and key-accessible by subj-group-type
        subj_group_nodes = node.getElementsByTagName('subj-group')
        for each in subj_group_nodes:
            type = each.getAttribute('subj-group-type')
            subj_list = []
            subj_nodes = each.getElementsByTagName('subject')
            for subj_node in subj_nodes:
                subj_list.append(getFormattedNode(subj_node))
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