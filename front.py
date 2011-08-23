

class Front(object):
    
    '''
    The metadata for an article, such as the name and issue of the journal 
    in which the article appears and the author(s) of the article
    '''
    
    def __init__(self, node):
        #Front may have no attributes
        self.root_tag = node
        
        #It must have a <journal-meta>
        journalmetanode = self.root_tag.getElementsByTagName('journal-meta')[0]
        
        #It must have a <article-meta>
        articlemetanode = self.root_tag.getElementsByTagName('article-meta')[0]
        
        