# -*- coding: utf-8 -*-

"""
openaccess_epub.article  defines abstract article representation

The openaccess_epub.article contains the :class:`Article` class which is
instantiated per article XML file. Basic article structural elements are
collected and metadata is parsed according to DTD rules into a python data
structure. The Article class forms a basic unit in the procedure of analyzing
articles and in the conversion to EPUB.
"""

#Standard Library modules
from collections import namedtuple
from keyword import iskeyword
import logging
import os
import shutil
import sys

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub import JPTS10_PATH, JPTS11_PATH, JPTS20_PATH,\
    JPTS21_PATH, JPTS22_PATH, JPTS23_PATH, JPTS30_PATH
from openaccess_epub.utils import element_methods

log = logging.getLogger('openaccess_epub.article')

dtd_tuple = namedtuple('DTD_Tuple', 'path, name, version')

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


class Article(object):
    """
    Abstract class for journal article; parses XML to data structure.

    The Article class operates on an abstract level to execute some common
    processing tasks for all journal articles. It first parses the journal
    article XML to an lxml.etree structure, then inspects the file to discover
    the appropriate DTD and version by which the article was published. It,
    optionally, validates the article according to its DTD then proceeds (if
    successful) to recursively parse all metadata into a tree data structure.
    This facilitates easy accession of nested elements using the following
    strategy: \"Article.metadata.front.journal_meta.publisher\"

    Parameters
    ----------
    xml_file : str
               Path to the xml file for parsing `xml_file`.
    validation : bool, optional
               DTD validation is used when this evaluates True, use is strongly
               advised `validation`.

    Attributes
    ----------
    doi : str
          The full DOI string for the article `doi`.
    dtd : lxml.etree.DTD object
          The parsed DTD object used for validation and metadata parsing `dtd`.
    dtd_name : str
          The name of the DTD, such as \"JPTS\" `dtd_name`.
    dtd_version : float
          The version of the DTD, such as 3.0 `dtd_version`.
    metadata : namedtuple object
          The metadata attribute is a tree structure of nested namedtuples.
          metadata itself holds two attributes, 'front' and 'back'. Each
          namedtuple under metadata will possess: attributes for every allowed
          child element defined by DTD, a dictionary of XML attributes held in
          the 'attrs' attribute, and a 'node' attribute for the lxml.etree
          Element itself. If any would-be attribute conflicts with a python
          keyword, it will be prepended by 'l' `metadata`.
    publisher : str
          A standardized, concise name for the publisher of the article, such as
          \"PLoS" or \"Frontiers" `publisher`.

    """
    def __init__(self, xml_file, validation=True):
        """
        The initialization of the Article class.
        """
        log.info('Parsing file: {0}'.format(xml_file))

        #Parse the document
        self.document = etree.parse(xml_file)

        #Find its public id so we can identify the appropriate DTD
        public_id = self.document.docinfo.public_id
        log.debug('Doctype PUBLIC: ' + public_id)

        #Instantiate an lxml.etree.DTD class from the dtd files in our data
        try:
            dtd = dtds[public_id]
        except KeyError as err:
            log.exception()
            log.error('Unkown DTD for value in Doctype PUBLIC: ' + public_id)
            raise err  # We can proceed no further without the DTD
        else:
            self.dtd = etree.DTD(dtd.path)
            self.dtd_name, self.dtd_version = dtd.name, dtd.version
            log.debug('DTD: {0} {1}'.format(self.dtd_name, self.dtd_version))

        #If using a supported DTD type, execute validation
        if validation:
            log.debug('DTD validation is in use')
            if not self.dtd.validate(self.document):
                log.critical('The document did not pass validation:\n' +
                             self.dtd.error_log.filter_from_errors())
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

        #Attempt, as well as possible, to identify the publisher and doi for
        #the article.
        self.doi = self.get_DOI()
        self.publisher = self.get_publisher()

    def get_metadata(self):

        #Dictionary comprehension - element name : element definition
        dtd_dict = {i.name: i for i in self.dtd.elements()}

        def coerce_string(input):
            for char in input:
                if char.lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_':
                    input = input.replace(char, '_')
            return input

        eltuple = namedtuple('ElTuple', 'tag, occurrence')

        def get_sub_elements(content, multiple=False, first=None):
            sub_elements = []  #The final list of tuples to be returned

            #The first level of recursion is special, and we need not be
            #concerned with inheriting plurality from an upper branch.
            if first:
                if content is None:
                    return []
                elif content.type == 'pcdata':
                    #If an element can only contain pcdata (text), look no more
                    return([eltuple('pcdata', 'multiple')])
                elif content.type in ['seq', 'or']:
                    if content.occur in ['mult', 'plus']:  # Pass on multiple
                        sub_elements += get_sub_elements(content, multiple=True)
                    else:  # Don't pass on multiple
                        sub_elements += get_sub_elements(content, multiple=False)
                elif content.type == 'element':  # May only contain one kind of element
                    if content.occur in ['mult', 'plus']:
                        return [eltuple(content.name, 'multiple')]
                    else:
                        return [eltuple(content.name, 'singular')]

            #This is for everything that is not the first point of recursion
            else:
                for branch in [content.left, content.right]:
                    if branch is not None:
                        #PCDATA is a special case, look no deeper, always multiple
                        if branch.type == 'pcdata':
                            sub_elements.append(eltuple('pcdata', 'multiple'))
                        #"seq" and "or" are sequence types, their plurality may
                        #be passed down to internal structures. Plurality is
                        #never lost, only gained.
                        elif branch.type in ['seq', 'or']:
                            if multiple or branch.occur in ['mult', 'plus']:
                                sub_elements += get_sub_elements(branch, multiple=True)
                            else:
                                sub_elements += get_sub_elements(branch, multiple=False)
                        elif branch.type == 'element':
                            if multiple or branch.occur in ['mult', 'plus']:
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
            sub_elements = get_sub_elements(element_def.content, first=True)
            get_text = False  # A control variable, used later if PCDATA in content model
            for sub_element in sub_elements:
                #We have the sub elements according to tag and occurrence
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
                field_vals.append(element_methods.all_text(element))

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
            return metadata_tuple(front, back)

    def get_publisher(self):
        """
        This function will attempt to identify the publisher of the article.
        """
        publisher_dois = {'10.1371': 'PLoS', '10.3389': 'Frontiers'}
        #Try to look up the publisher by DOI
        if self.doi:
            try:
                publisher = publisher_dois[self.doi.split('/')[0]]
            except KeyError:
                log.info('publisher DOI not recognized:' + self.doi)
            else:
                return publisher
        #If that fails, attempt to extract the publisher through inspection
        if self.dtd_name == 'JPTS':
            publisher_meta = self.metadata.front.journal_meta.publisher
            if publisher_meta is not None:  # Optional element
                log.debug('publisher element in journal-meta found')
                name_text = publisher_meta.publishder_name.text
                log.debug('publisher name: ' + publisher_name)
                if name_text == 'Public Library of Science':
                    return 'PLoS'
                elif name_text == 'Frontiers Media S.A.':
                    return 'Frontiers'
        log.warning('Unable to identify publisher for this article!')
        return None

    def get_DOI(self):
        """
        This function will attempt to locate the DOI string associated with the
        article.
        """
        if self.dtd_name == 'JPTS':
            art_ids = self.metadata.front.article_meta.article_id
            for art_id in art_ids:
                if art_id.attrs['pub-id-type'] == 'doi':
                    return art_id.text
            log.warning('Unable to locate DOI string for this article')
            return None
        else:
            log.warning('Unable to locate DOI string for this article')
            return None
