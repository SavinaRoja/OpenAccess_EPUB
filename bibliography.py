"""biblio: creates a list of bibliographical references"""
import reference
import logging
from utils import OUT_DIR
import utils
import os.path

class Biblio(object):
    """Article bibliography
    doc -- output of lxml.etree.parse('article.xml')
    """
    def __init__(self, doc):
        back = doc.getElementsByTagName('back')[0]
        reflist = back.getElementsByTagName('ref-list')[0]
        self.reftaglist = reflist.getElementsByTagName('ref')
        self.bibliography = []
        
        for ref in self.reftaglist:
            refid = ref.getAttribute('id')
            citationnode = ref.getElementsByTagName('citation')[0]
            citationtype = citationnode.getAttribute('citation-type')
            citation = None
            if citationtype == 'journal':
                citation = reference.Journal(ref, refid)
            else:
                citation = reference.Reference(ref, refid)
            self.bibliography.append(citation)
            logging.debug(citation)
            
    def output(self):
        
        doc, body = utils.initiateDocument('References')
        
        header = doc.createElement('h3')
        header.appendChild(doc.createTextNode('References:'))
        body.appendChild(header)
        
        for entry in self.bibliography:
            ref = doc.createElement('ref')
            ref.setAttribute('id', entry.id)
            p = doc.createElement('p')
            ref.appendChild(p)
            text = doc.createTextNode(entry.__str__())
            p.appendChild(text)
            body.appendChild(ref)
        
        #To enable logging for this function, uncomment the line below
        #logging.debug(doc.toprettyxml(encoding='UTF-8'))
        
        #To enable output for this function, uncomment the lines below
        xml_file = os.path.join(OUT_DIR, 'references.xml')
        with open(xml_file, 'w') as outdoc:
            outdoc.write(doc.toprettyxml(encoding = 'UTF-8'))
