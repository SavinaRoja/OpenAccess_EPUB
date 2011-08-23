
class Article(object):
    '''A journal article; the top-level element (document element) of the 
    Journal Publishing DTD, which contains all the metadata and content for 
    the article
    
    http://dtd.nlm.nih.gov/publishing/tag-library/2.0/index.html
    '''
    
    def __init__(self, doc):
        self.root_tag = doc.documentElement
        
        attr_strings = [u'article-type', u'dtd-version', u'xml:lang', u'xmlns:mml', u'xmlns:xlink']
        
        self.attributes = {}
        
        for attr in attr_strings:
            value = self.root_tag.getAttribute(attr)
            self.attributes[attr] = value
            
        print(self.attributes)
            
        if self.attributes[u'xmlns:mml'] != u'http://www.w3.org/1998/Math/MathML':
            raise ValueError('The MathML attribute value may not be changed from \'http://www.w3.org/1998/Math/MathML\'')
        
        if self.attributes[u'xmlns:xlink'] != u'http://www.w3.org/1999/xlink':
            raise ValueError('The XLink Namespace Declaration attribute value may not be changed from \'http://www.w3.org/1999/xlink\'')
        
        if self.attributes[u'dtd-version'] != u'2.0':
            raise ValueError('Version 2.0 of the Journal Publishing DTD must be used')