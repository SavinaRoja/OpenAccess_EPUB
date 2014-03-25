# -*- coding: utf-8 -*-

"""
openaccess_epub.navigation provides facilities for producing EPUB navigation
documents

The Navigation Document is a required component of an EPUB document in both
EPUB2 and EPUB3. OpenAccess_EPUB provides support for both EPUB versions with
this module. The Navigation class can work with either a single article or with
multiple articles. The processing of articles for important navigation mapping
is currently publisher agnostic, however since this document also utilizes (a
very limited subset of) metadata , there will be some amount of
publisher-specific metadata methods required.
"""

#This module will be superceding the previouse ncx module. It will become more
#general and capable of producing navigation for EPUB2, and EPUB3.

#Standard Library modules
from collections import namedtuple
import logging

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub.utils import OrderedSet
import openaccess_epub.utils.element_methods as element_methods

log = logging.getLogger('openaccess_epub.navigation')

navpoint = namedtuple('navpoint', 'id, label, playOrder, source, children')


class Navigation(object):

    def __init__(self, collection=False):
        self.collection = collection

        #Special navigation structures: List of Equations/Figures/Tables
        self.equations_list = []
        self.figures_list = []
        self.tables_list = []

        #all_articles is only used for collection mode
        self.article = None

        #These are the limited forms of metadata that might make it in to the
        #navigation document. Both are used for EPUB2, only the title is used
        #for EPUB3
        self.title = 'Navigation Document for:'
        self.authors = OrderedSet()

        #The nav structure is a list of navpoint trees. Each navpoint may have
        #children navpoints. This structure will be converted to the appropriate
        #xml/xhtml structure and written to file when required.
        self.nav = []
        self.nav_depth = 0

        self._play_order = 0
        self._auto_id = 0

    def process(self, article):
        """
        Ingests an Article to create navigation structures and parse global
        metadata.
        """
        if self.article is not None and not self.collection:
            log.warning('Could not process additional article. Navigation only \
handles one article unless collection mode is set.')
            return False

        self.article = article
        self.article_doi = self.article.doi.split('/')[1]
        if self.collection:
            self.title += ' ' + self.article.doi
        else:
            self.title += self.article.publisher.nav_title(article)
        for author in self.article.publisher.nav_creators(article):
            self.authors.add(author)

        #Analyze the structure of the article to create internal mapping
        self.map_navigation()

    def map_navigation(self):
        """
        This is a wrapper for depth-first recursive analysis of the article
        """
        #All articles should have titles
        title_id = 'titlepage-{0}'.format(self.article_doi)
        title_label = 'This is a title'  # TODO: Make this real
        title_source = 'main.{0}.xhtml#title'.format(self.article_doi)
        title_navpoint = navpoint(title_id, title_label, self.play_order,
                                  title_source, [])
        #When processing a collection of articles, we will want all subsequent
        #navpoints for this article to be located under the title
        if self.collection:
            nav_insertion = title_navpoint.children
        else:
            nav_insertion = self.nav

        #If the article has a body, we'll need to parse it for navigation
        if self.article.body is not None:
            #Pre-process the article to assign ids if missing
            #for section in self.article.body.findall('.//sec'):
                #if 'id' not in section.attrib:
                    #section.attrib['id'] = self.auto_id()
            #Here is where we invoke the recursive parsing!
            for nav_pt in self.recursive_article_navmap(self.article.body):
                nav_insertion.append(nav_pt)

        #Add a navpoint to the references if appropriate
        if self.article.back is not None:
            if self.article.back.findall('ref'):
                ref_id = 'references-{0}'.format(self.article_doi)
                ref_label = 'References'
                ref_source = 'biblio.{0}.xhtml#references'.format(self.article_doi)
                ref_navpoint = navpoint(ref_id, ref_label, self.play_order,
                                        ref_source, [])
                nav_insertion.append(ref_navpoint)

    def recursive_article_navmap(self, src_element, depth=0, first=True):
        """
        This function recursively traverses the content of an input article to
        add the correct elements to the NCX file's navMap and Lists.
        """
        if depth > self.nav_depth:
            self.nav_depth = depth
        navpoints = []
        tagnames = ['sec', 'fig', 'table-wrap']
        for child in src_element:
            try:
                tagname = child.tag
            except AttributeError:  # Text nodes have no attribute tagName
                continue
            else:
                if tagname not in tagnames:
                    continue

            #Safely handle missing id attributes
            if 'id' not in child.attrib:
                child.attrib['id'] = self.auto_id

            #If in collection mode, we'll prepend the article DOI to avoid
            #collisions
            if self.collection:
                child.attrib['id'] = '-'.join(self.article_doi,
                                              child.attrib['id'])

            #Attempt to infer the correct text as a label
            #Skip the element if we cannot
            child_title = child.find('title')
            if child_title is None:
                continue  # If there is no immediate title, skip this element
            label = element_methods.all_text(child_title)
            if not label:
                continue  # If no text in the title, skip this element
            source = 'main.{0}.xhtml#{1}'.format(self.article_doi,
                                               child.attrib['id'])
            if tagname == 'sec':
                children = self.recursive_article_navmap(child, depth=depth + 1)
                navpoints.append(navpoint(child.attrib['id'],
                                          label,
                                          self.play_order,
                                          source,
                                          children))
            #figs and table-wraps do not have children
            elif tagname == 'fig':  # Add navpoints to list_of_figures
                self.figures_list.append(navpoint(child.attrib['id'],
                                                  label,
                                                  None,
                                                  source,
                                                  []))
            elif tagname == 'table-wrap':  # Add navpoints to list_of_tables
                self.tables_list.append(navpoint(child.attrib['id'],
                                                 label,
                                                 None,
                                                 source,
                                                 []))
        return navpoints

    def render_EPUB2(self, location):
        pass

    def render_EPUB3(self, location, back_compat=False):
        pass
        if back_compat:
            self.render_EPUB2(location)

    @property
    def play_order(self):
        self._play_order += 1
        return self._play_order

    @property
    def auto_id(self):
        self._auto_id += 1
        id_gen = 'OAE-{0}'.format(self._auto_id)
        log.debug('Navigation element missing ID: assigned {0}'.format(id_gen))
        return id_gen
