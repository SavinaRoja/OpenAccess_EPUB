# -*- coding: utf-8 -*-
import openaccess_epub.utils.element_methods as element_methods
import openaccess_epub.utils as utils
from openaccess_epub.jpts.jptsmetadata import JPTSMetaData20,\
    JPTSMetaData23, JPTSMetaData30
from openaccess_epub import JPTS10_PATH, JPTS11_PATH, JPTS20_PATH,\
    JPTS21_PATH, JPTS22_PATH, JPTS23_PATH, JPTS30_PATH
import os
import sys
import shutil
import xml.dom.minidom as minidom
#lxml shall fully replace minidom eventually
from lxml import etree
import logging
from collections import namedtuple
from keyword import iskeyword


log = logging.getLogger('Article')


dtd_tuple = namedtuple('DTD_Tuple', 'path, name, version ')

dtds = {'-//NLM//DTD Journal Archiving and Interchange DTD v1.0 20021201//EN':
        dtd_tuple(JPTS10_PATH, 'JPTS', 1.0),
        '-//NLM//DTD Journal Archiving and Interchange DTD v1.1 20031101//EN':
        dtd_tuple(JPTS11_PATH, 'JPTS', 1.1),
        '-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN':
        dtd_tuple(JPTS20_PATH, 'JPTS', 2.0),
        '-//NLM//DTD Journal Publishing DTD v2.1 20050630//EN':
        dtd_tuple(JPTS21_PATH, 'JPTS', 2.1),
        '-//NLM//DTD Journal Publishing DTD v2.2 20060430//EN':
        dtd_tuple(JPTS22_PATH, 'JPTS', 2.2),
        '-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN':
        dtd_tuple(JPTS23_PATH, 'JPTS', 2.3),
        '-//NLM//DTD Journal Publishing DTD v3.0 20080202//EN':
        dtd_tuple(JPTS30_PATH, 'JPTS', 3.0)}


class Article2(object):
    """
    At this stage, the journal article is parsed by lxml, validated against its
    DTD version, and then will have its metadata elements parsed into a
    hierarchical namedtuple structure. Additional metadata abstractions may
    also be implemented. This class will be later passed to OPF and NCX for
    structural/metadata translation and to OPS for content translation.
    """
    def __init__(self, xml_file):
        log.info('Parsing file: {0}'.format(xml_file))
        #Parse the document
        self.document = etree.parse(xml_file)
        #Find its public id so we can identify the appropriate DTD
        public_id = self.document.docinfo.public_id
        #Instantiate an lxml.etree.DTD class from the dtd files in our data
        try:
            dtd = dtds[public_id]
        except KeyError as err:
            print('Document published according to unsupported specification. \
Please contact the maintainers of OpenAccess_EPUB.')
            raise err  # We can proceed no further without the DTD
        else:
            self.dtd = etree.DTD(dtd.path)
            self.dtd_name, self.dtd_version = dtd.name, dtd.version
        #If using a supported DTD type, execute validation
        validated = self.dtd.validate(self.document)
        if not validated:
            print('The document {0} did not pass validation according to its \
DTD.'.format(xml_file))
            print(self.dtd.error_log.filter_from_errors())
            sys.exit(1)
        #Get basic elements, per DTD (and version if necessary)
        if self.dtd_name == 'JPTS':
            self.front = self.document.find('front')  # Element: mandatory
            self.body = self.document.find('body')  # Element or None
            self.back = self.document.find('back')  # Element or None
            self.sub_article = self.document.findall('sub-article')  # 0 or more
            self.response = self.document.findall('response')  # 0 or more
        
        #At this point we have parsed the article, validated it, defined key
        #top-level elements in it, and now we must translate its metadata into
        #a data structure.
        self.metadata = self.get_metadata()

    def get_metadata(self):
        
        #Dictionary comprehension - element name : element definition
        dtd_dict = {i.name: i for i in self.dtd.elements()}
        
        def coerce_string(input):
            for char in input:
                if char.lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_':
                    input = input.replace(char, '_')
            return input
        
        eltuple = namedtuple('ElTuple', 'tag, occurrence')
        
        def get_sub_elements(content, multiple=False):
            if content is None:
                return []
            sub_elements = []
            left, right = content.left, content.right
            for branch in [left, right]:
                if branch:
                    #PCDATA is a special case, it is always multiple, and it
                    #has no possible sub-elements
                    if branch.type == 'pcdata':
                        sub_elements.append(eltuple('pcdata', 'multiple'))
                    #For our purposes, both "seq" and "or" types are sequences
                    #If a sequence component occurrence is mult or plus, then
                    #every internal component should inherit plurality that may
                    #not be overridden
                    #If a sequence component occurence is once or opt, then
                    #every internal component should inherit singularity, but
                    #this singularity may be overridden to plural.
                    #Plurality is passed on through the multiple argument
                    elif branch.type in ['seq', 'or']:
                        if branch.occur in ['mult', 'plus']:
                            sub_elements += get_sub_elements(branch, multiple=True)
                        else:
                            sub_elements += get_sub_elements(branch, multiple=False)
                    else:  # element
                        #If an element inherits plurality, it will stay plural
                        if multiple is True:
                            sub_elements.append(eltuple(branch.name, 'multiple'))
                        #If an element inherits singularity, it should check to
                        #see if it overrides to plural
                        else:
                            occurrence = branch.occur
                            if occurrence in ['mult', 'plus']:
                                sub_elements.append(eltuple(branch.name, 'multiple'))
                            else:
                                sub_elements.append(eltuple(branch.name, 'singular'))
            return sub_elements
        
        def recursive_element_packing(element):
            if element is None:
                return None
            tagname = element.tag
            element_def = dtd_dict[tagname]
            #Create lists for field names and field values
            field_names = []
            field_vals = []
            #Create a self reference, named node, value is the element itself
            field_names.append('node')
            field_vals.append(element)
            #Handle attributes
            attrs = {}  # Dict to hold attributes
            field_names.append('attrs')  # namedtuple attribute to receive dict
            #Compose the attrs dict with appropriate keys and values
            for attribute in element_def.iterattributes():
                if attribute.prefix:
                    if attribute.prefix == 'xmlns':  # Pseudo-attribute
                        continue
                    elif attribute.prefix == 'xml':
                        attr_lookup = '{{http://www.w3.org/XML/1998/namespace}}{0}'.format(attribute.name)
                    else:
                        attr_lookup = '{'+element.nsmap[attribute.prefix]+'}'+attribute.name
                    key = '{0}:{1}'.format(attribute.prefix, attribute.name)
                else:
                    key = attribute.name
                    attr_lookup = key
                #Add the value of the attribute to list of field values
                try:
                    value = element.attrib[attr_lookup]
                except KeyError:
                    attrs[key] = None  # Not worrying about implied defaults right now
                    #field_vals.append(None
                else:
                    attrs[key] = value
            #Add the attrs dict to field values
            field_vals.append(attrs)
            #Get the sub_elements for the element
            sub_elements = get_sub_elements(element_def.content)
            get_text = False  # A control variable, used later if PCDATA in content model
            for sub_element in sub_elements:
                #We have the sub elements according to tag and occurence
                if sub_element.tag == 'pcdata':
                    get_text = True
                    continue
                if sub_element.occurrence == 'multiple':
                    child_tag = sub_element.tag
                    child_list = []
                    for each in element.findall(child_tag):
                        child_list.append(recursive_element_packing(each))
                    field_names.append(child_tag)
                    field_vals.append(child_list)
                else:
                    child_tag = sub_element.tag
                    child_element = element.find(child_tag)
                    if child_element is not None:
                        child = recursive_element_packing(child_element)
                    else:
                        child = None
                    field_names.append(child_tag)
                    field_vals.append(child)
            if get_text:
                field_names.append('text')
                field_vals.append(etree.tostring(element, method='text', encoding='utf-8').strip())

            #Make items in field_names safe for namedtuple
            #Coerce characters in string
            field_names = [coerce_string(i) for i in field_names]
            #Prepend 'l' to reserved keywords for element tagname
            if iskeyword(tagname):
                tagname = 'l' + tagname
            #Prepend 'l' to reserved keywords for sub_elements
            field_names = ['l'+i if iskeyword(i) else i for i in field_names]

            data_tuple = namedtuple(coerce_string(tagname), ', '.join(field_names))
            return data_tuple(*field_vals)

        if self.dtd_name == 'JPTS':
            metadata_tuple = namedtuple('Metadata', 'front, back')
            front = recursive_element_packing(self.front)
            back = recursive_element_packing(self.back)
            #test_root = recursive_element_packing(self.document.getroot())
            return metadata_tuple(front, back)

    def get_publisher(self):
        return None

    def get_DOI(self):
        return None

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
        publisher using self.identify_publisher(). It is responsible for
        using this information to create an instance of a metadata class
        such as found in jptsmeta.py to serve as the article's metadata
        attribute.
        """
        log.info('Parsing file - {0}'.format(xml_file))
        doc = minidom.parse(xml_file)
        #Here we check the doctype for the DTD under which the article was
        #published. This affects how we will parse metadata and content.
        dtds={'-//NLM//DTD Journal Archiving and Interchange DTD v1.0 20021201//EN':
              '1.0',
              '-//NLM//DTD Journal Archiving and Interchange DTD v1.1 20031101//EN':
              '1.1',
              '-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN':
              '2.0',
              '-//NLM//DTD Journal Publishing DTD v2.1 20050630//EN':
              '2.1',
              '-//NLM//DTD Journal Publishing DTD v2.2 20060430//EN':
              '2.2',
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
        self.publisher = self.identify_publisher()
        log.info('Publisher - {0}'.format(self.publisher))
        #Create instance of article metadata
        if self.dtd == '2.0':
            self.metadata = JPTSMetaData20(doc, self.publisher)
        elif self.dtd == '2.3':
            self.metadata = JPTSMetaData23(doc, self.publisher)
        elif self.dtd == '3.0':
            self.metadata = JPTSMetaData30(doc, self.publisher)
        #The <article> tag has a handful of potential attributes, we can check
        #to make sure the mandated ones are valid
        self.attrs = {'article-type': None, 'dtd-version': None,
                      'xml:lang': None, 'xmlns:mml': None,
                      'xmlns:xlink': None, 'xmlns:xsi': None}
        for attr in self.attrs:
            #getAttribute() returns an empty string if the attribute DNE
            self.attrs[attr] = self.root_tag.getAttribute(attr)
        self.validate_attributes()  # Log errors for invalid attribute values
        try:
            self.body = self.root_tag.getElementsByTagName('body')[0]
        except IndexError:
            self.body = None

    def identify_publisher(self):
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

    def validate_attributes(self):
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
        for key, val in mandates:
            if self.attrs[key] and not self.attrs[key] == val:
                log.error(attr_err.format(key, self.attrs[key]))
        if self.attrs['article-type'] not in utils.suggested_article_types:
            art_type_err = 'article-type value is not a suggested value - {0}'
            log.warning(art_type_err.format(self.attrs['article-type']))

    def get_DOI(self):
        """
        A method for returning the DOI identifier of an article
        """
        return self.metadata.article_id['doi']
