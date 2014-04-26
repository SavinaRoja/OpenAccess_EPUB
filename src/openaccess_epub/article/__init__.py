# -*- coding: utf-8 -*-

"""
openaccess_epub.article defines abstract article representation

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
from openaccess_epub.utils import element_methods, publisher_plugin_location
import openaccess_epub.publisher

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
        DTD validation is used when this evaluates True, use is strongly advised
        `validation`.

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
        The metadata attribute is a tree structure of nested namedtuples. For
        JPTS the metadata holds two attributes, 'front' and 'back'. Each
        namedtuple under metadata will possess: attributes for every allowed
        child element defined by DTD, a dictionary of XML attributes held in the
        'attrs' attribute, and a 'node' attribute for the lxml.etree Element
        itself. If any would-be attribute conflicts with a python keyword, it
        will be prepended by 'l' `metadata`.
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
        parser = etree.XMLParser(remove_blank_text=True)
        self.document = etree.parse(xml_file, parser)

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

        self.root = self.document.getroot()
        self.body = self.root.find('body')

        #Attempt, as well as possible, to identify the publisher and doi for
        #the article.
        self.doi = self.get_DOI()
        self.publisher = self.get_publisher()

    def get_publisher(self):
        """
        This method defines how the Article tries to determine the publisher of
        the article.

        This method relies on the success of the get_DOI method to fetch the
        appropriate full DOI for the article. It then takes the DOI prefix
        which corresponds to the publisher and then uses that to attempt to load
        the correct publisher-specific code. This may fail; if the DOI is not
        mapped to a code file, if the DOI is mapped but the code file could not
        be located, or if the mapped code file is malformed then this method
        will issue/log an informative error message and return None. This method
        will not try to infer the publisher based on any metadata other than the
        DOI of the article.

        Returns
        -------
        publisher : Publisher instance or None
        """
        #For a detailed explanation of the DOI system, visit:
        #http://www.doi.org/hb.html
        #The basic syntax of a DOI is this <prefix>/<suffix>
        #The <prefix> specifies a unique DOI registrant, in our case, this
        #should correspond to the publisher. We use this information to register
        #the correct Publisher class with this article
        doi_prefix = self.doi.split('/')[0]
        #The import_by_doi method should raise ImportError if a problem occurred
        try:
            publisher_mod = openaccess_epub.publisher.import_by_doi(doi_prefix)
        except ImportError as e:
            log.exception(e)
            return None
        #Each publisher module should define an attribute "pub_class" pointing
        #to the publisher-specific class extending
        #openaccess_epub.publisher.Publisher
        return publisher_mod.pub_class(self)

    def get_DOI(self):
        """
        This method defines how the Article tries to detect the DOI.

        It attempts to determine the article DOI string by DTD-appropriate
        inspection of the article metadata. This method should be made as
        flexible as necessary to properly collect the DOI for any XML
        publishing specification.

        Returns
        -------
        doi : str or None
            The full (publisher/article) DOI string for the article, or None on
            failure.
        """
        if self.dtd_name == 'JPTS':
            doi = self.root.xpath("./front/article-meta/article-id[@pub-id-type='doi']")
            if doi:
                return doi[0].text
            log.warning('Unable to locate DOI string for this article')
            return None
        else:
            log.warning('Unable to locate DOI string for this article')
            return None
