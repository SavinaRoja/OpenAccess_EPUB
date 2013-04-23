# -*- coding: utf-8 -*-
import utils.element_methods
import os.path
import sys
import shutil
import xml.dom.minidom as minidom
import jpts
import urllib2
import logging
from time import sleep

log = logging.getLogger('Article')

#Monkey patching in some extended methods for xml.dom.minidom classes
minidom.Node.removeSelf = utils.element_methods.removeSelf
minidom.Node.replaceSelfWith = utils.element_methods.replaceSelfWith
minidom.Node.elevateNode = utils.element_methods.elevateNode
minidom.Element.getChildrenByTagName = utils.element_methods.getChildrenByTagName
minidom.Element.removeAllAttributes = utils.element_methods.removeAllAttributes
minidom.Element.getAllAttributes = utils.element_methods.getAllAttributes


class Article(object):
    """
    A journal article; the top-level element (document element) of the
    Journal Publishing DTD, which contains all the metadata and content for
    the article.
    3.0 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/3.0/n-3q20.html
    2.0 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-9kc0.html
    2.3 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/2.3/n-zxc2.html
    """
    def __init__(self, xml_file):
        """
        The __init__() method has to do the following specific jobs. It must
        parse the article using xml.dom.minidom. It must check the parsed
        article to detect its DTD and version; it must also detect the
        publisher using self.identifyPublisher(). It is responsible for
        using this information to create an instance of a metadata class
        such as found in jptsmeta.py to serve as the article's metadata
        attribute.
        """
        log.info('Parsing file - {0}'.format(xml_file))
        doc = minidom.parse(xml_file)
        #Here we check the doctype for the DTD under which the article was
        #published. This affects how we will parse metadata and content.
        dtds = {'-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN':
                '2.0',
                '-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN':
                '2.3',
                '-//NLM//DTD Journal Publishing DTD v3.0 20080202//EN':
                '3.0'}
        try:
            self.dtd = dtds[doc.doctype.publicId]
            dtdStatus = 'Article published with Journal Publishing DTD v{0}'
            log.debug(dtdStatus.format(self.dtd))
        except KeyError:
            print('The article\'s DOCTYPE declares an unsupported Journal \
Publishing DTD: \n{0}'.format(doc.doctype.publicId))
            sys.exit()
        #Access the root tag of the document name
        self.root_tag = doc.documentElement
        #Determine the publisher
        self.publisher = self.identifyPublisher()
        log.info('Publisher - {0}'.format(self.publisher))
        #Create instance of article metadata
        if self.dtd == '2.0':
            self.metadata = jpts.JPTSMeta20(doc, self.publisher)
        elif self.dtd == '2.3':
            self.metadata = jpts.JPTSMeta23(doc, self.publisher)
        elif self.dtd == '3.0':
            self.metadata = jpts.JPTSMeta30(doc, self.publisher)
        #The <article> tag has a handful of potential attributes, we can check
        #to make sure the mandated ones are valid
        self.attrs = {'article-type': None, 'dtd-version': None,
                      'xml:lang': None, 'xmlns:mml': None,
                      'xmlns:xlink': None, 'xmlns:xsi': None}
        for attr in self.attrs:
            #getAttribute() returns an empty string if the attribute DNE
            self.attrs[attr] = self.root_tag.getAttribute(attr)
        self.validateAttrs()  # Log errors for invalid attribute values
        try:
            self.body = self.root_tag.getElementsByTagName('body')[0]
        except IndexError:
            self.body = None

    def identifyPublisher(self):
        """
        This method determines the publisher of the document based on an
        an internal declaration. For both JP-DTDv2.0 and JP-DTDv2.3, there are
        two important signifiers of publisher, <publisher> under <journal-meta>
        and <article-id pub-id-type="doi"> under <article-meta>.
        """
        log.info('Determining Publisher')
        pubs = {'Frontiers Research Foundation': 'Frontiers',
                'Public Library of Science': 'PLoS'}
        dois = {'10.3389': 'Frontiers',
                '10.1371': 'PLoS'}
        if self.dtd in ['2.0', '2.3']:
            #The publisher node will be the primary mode of identification
            publisher = self.root_tag.getElementsByTagName('publisher')
            pname = False
            if publisher:
                log.debug('Located publisher element')
                pname = publisher[0].getElementsByTagName('publisher-name')[0]
                pname = pname.firstChild.data
                try:
                    return pubs[pname]
                except KeyError:
                    log.debug('Strange publisher name - {0}'.format(pname))
                    log.debug('Falling back to article-id DOI')
                    pname = False
            if not pname:  # If pname is undeclared, check article-id
                art_IDs = self.root_tag.getElementsByTagName('article-id')
                for aid in art_IDs:
                    if aid.getAttribute('pub-id-type') == 'doi':
                        idstring = aid.firstChild.data
                        pub_doi = idstring.split('/')[0]
                try:
                    return dois[pub_doi]
                except KeyError:
                    print('Unable to identify publisher by DOI, aborting!')
                    sys.exit()

    def validateAttrs(self):
        """
        Most of the time, attributes are not required nor do they have fixed
        values. But in this case, there are some mandatory requirements.
        """
        #I would love to check xml:lang against RFC 4646:
        # http://www.ietf.org/rfc/rfc4646.txt
        #I don't know a good tool for it though, so it gets a pass for now.
        mandates = [('xmlns:mml', 'http://www.w3.org/1998/Math/MathML'),
                    ('xmlns:xlink', 'http://www.w3.org/1999/xlink'),
                    ('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')]
        attr_err = 'Article attribute {0} has improper value: {1}'
        for _key, _val in mandates:
            if self.attrs[_key] and not self.attrs[_key] == _val:
                log.error(attr_err.format(_key, self.attrs[_key]))
        if self.attrs['article-type'] not in utils.suggestedArticleTypes():
            art_type_err = 'article-type value is not a suggested value - {0}'
            log.warning(art_type_err.format(self.attrs['article-type']))

    def getDOI(self):
        """
        A method for returning the DOI identifier of an article
        """
        return self.metadata.article_id['doi']
