import front, body, back


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
        
        
        if self.attributes[u'xmlns:mml'] != u'http://www.w3.org/1998/Math/MathML':
            print('ERROR: The MathML attribute value may not be changed from \'http://www.w3.org/1998/Math/MathML\'')
        
        if self.attributes[u'xmlns:xlink'] != u'http://www.w3.org/1999/xlink':
            print('ERROR: The XLink Namespace Declaration attribute value may not be changed from \'http://www.w3.org/1999/xlink\'')
        
        #Mandatory
        frontnode = self.root_tag.getElementsByTagName(u'front')[0]
        
        #Technically optional, but assume for now that they will be present
        bodynode = self.root_tag.getElementsByTagName('body')[0]
        backnode = self.root_tag.getElementsByTagName('back')[0]
        
        #It can have a <sub-article> or a <response>, but let's ignore that for now
        #try:
        #    subarticlenode = self.root_tag.getElementsByTagName('sub-article')[0]
        #except:
        #    try:
        #        responsenode = self.root_tag.getElementsByTagName('response')[0]
        #    except:
        #        pass
        
        self.front = front.Front(frontnode)
        self.body = body.Body(bodynode)
        self.back = back.Back(backnode)
        