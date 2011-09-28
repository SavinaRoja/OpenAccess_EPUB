import xml.dom.minidom as minidom
import os, os.path

class OPSContent(object):
    '''A class for instantiating content xml documents in the OPS Preferred
    Vocabulary'''
    def __init__(self, documentstring, outdirect, metadata):
        self.inputstring = documentstring
        self.doc = minidom.parse(self.inputstring)
        self.outputs = {'Synopsis': os.path.join(outdirect, 'synop.xml'), 
                        'Main': os.path.join(outdirect, 'main.xml'), 
                        'Biblio': os.path.join(outdirect, 'biblio.xml')}
        self.metadata = metadata
        
    def createSynopsis(self):
        '''Create an output file containing a representation of the article 
        synopsis'''
        pass
    
    def createMain(self):
        '''Create an output file containing the main article body content'''
        pass
    
    def createBiblio(self):
        '''Create an output file containing the article bibliography'''
        pass