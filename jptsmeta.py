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

class JPTSMeta(object):
    """
    This is the base class for the Journal Publishing Tag Set metadata.
    """
    def __init__(self, document, publisher):
        self.doc = document
        self.publisher = publisher
        self.getTopElements()
    
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
    
    def dtdVersion(self):
        return None


class JPTSMeta20(JPTSMeta):
    """
    This is the derived class for version 2.0 of the Journal Publishing Tag Set
    metadata.
    """
    
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
    
    def dtdVersion(self): 
        return '3.0'
