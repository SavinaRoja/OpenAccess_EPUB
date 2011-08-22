"""Handles metadata related tasks for the article"""
import logging
from article import ArticleMeta
from journal import JournalMeta
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