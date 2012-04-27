"""
This module contains classes representing metadata in the Journal Publishing
Tag Set. There is a base class providing a baseline of functionality for the
JPTS and derived classes for distinct version of the Tag Set. With this
implementation, the commonalities between versions may be presented in the base
class while their differences may be presented in their derived classes. An
important distinction is to be made between publisher and the DTD version; for
full extensibility in development, they are unique parameters.
"""

class JPTSMeta(object):
    """
    This is the base class for the Journal Publishing Tag Set metadata.
    """
    def __init__(self):
        self.data = 'Hello world'
    
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
    def dtdVersion(self):
        return '2.3'


class JPTSMeta30(JPTSMeta):
    """
    This is the derived class for version 3.0 of the Journal Publishing Tag Set
    metadata.
    """
    def dtdVersion(self):
        return '3.0'
