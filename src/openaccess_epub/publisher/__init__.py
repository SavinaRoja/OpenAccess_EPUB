# -*- coding: utf-8 -*-

"""
openaccess_epub.publisher defines abstract publisher representation and content
conversion
"""

#Standard Library modules
import os
from collections import namedtuple
from copy import copy, deepcopy
from importlib import import_module
import logging
import sys
try:
    from importlib.abc import SourceLoader
except ImportError:  # Compatibility for Python 3.0 and 3.1
    from importlib.abc import PyLoader as SourceLoader
import weakref

#Non-Standard Library modules
from lxml import etree

#OpenAccess_EPUB modules
from openaccess_epub.utils.element_methods import *
from openaccess_epub.utils import publisher_plugin_location

__all__ = ['contributor_tuple', 'date_tuple', 'identifier_tuple',
           'import_by_doi', 'Publisher']

log = logging.getLogger('openaccess_epub.publisher')

contributor_tuple = namedtuple('Contributor', 'name, role, file_as')
date_tuple = namedtuple('Date', 'year, month, day, season, event')
identifier_tuple = namedtuple('Identifier', 'value, scheme')


### Section Start - Dynamic Extension with publisher_plugins folder ############
################################################################################
#The code in this section is devoting to creating easy publisher-wise extension
#for rapid testing and development without modifying installed source
plugin_dir = publisher_plugin_location()
doi_map_file = os.path.join(plugin_dir, 'doi_map')

doi_map = {'10.1371': 'plos',
           '10.3389': 'frontiers'}

#By inserting at the beginning, the plugin directory will override the source
#modules if they exist
__path__.insert(0, publisher_plugin_location())

if not os.path.isfile(doi_map_file):
    os.makedirs(os.path.dirname(doi_map_file))
    with open(doi_map_file, 'a'):
        os.utime(doi_map_file, None)

with open(doi_map_file, 'r') as mapping:
    for line in mapping:
        key, val = line.split(':')
        doi_map[key.strip()] = val.strip()


class PublisherFinder(object):
    prefix = 'openaccess_epub.publisher'

    def __init__(self, path_entry):
        if path_entry not in __path__:
            raise ImportError
        else:
            self.path_entry = path_entry
            return None

    def find_module(self, fullname, path=None):
        path = path or self.path_entry
        name = fullname.split('.')[-1]
        for fname in [os.path.join(i, name + '.py') for i in __path__]:
            if os.path.isfile(fname):
                return PublisherLoader(path)
        return None


class PublisherLoader(SourceLoader):

    def __init__(self, path_entry):
        self.path_entry = path_entry
        return None

    #This is poorly documented, the argument to get_data is implicitly supplied
    #by a call to get_filename
    def get_data(self, filepath):
        with open(filepath, 'r') as source:
            return bytes(source.read(), 'utf-8')

    def get_filename(self, path):
        name = path.split('.')[-1]
        for fname in [os.path.join(i, name + '.py') for i in __path__]:
            if os.path.isfile(fname):
                return fname
        return None

sys.path_hooks.append(PublisherFinder)


def import_by_doi(doi):
    try:
        mod_name = doi_map[doi]
    except KeyError:  # Informative recasting of KeyError to ImportError
        raise ImportError('DOI publisher prefix "{0}" not mapped to module name'.format(doi))
    module = import_module('.'.join([__name__, mod_name]))
    return module
### Section End - Dynamic Extension with publisher_plugins folder ##############
################################################################################


def func_registrar():
    func_list = []

    def register(func):
        func_list.append(func)
        return func
    register.all = func_list
    return register


class Publisher(object):
    """
    Meta class for publishers, sub-class per publisher to add support
    """

    #Maker methods are for generating content
    maker2 = func_registrar()  # EPUB2 methods
    maker3 = func_registrar()  # EPUB3 methods

    #Special methods are for elegant pre-processing, prior to ignorant recursive
    #iteration through the document tree to convert elements
    special2 = func_registrar()  # EPUB2 methods
    special3 = func_registrar()  # EPUB3 methods

    def __init__(self, article):
        """
        The initialization of the Publisher class.
        """
        self.article = article

        article_doi = '/'.join(self.article.doi.split('/')[1:])

        self.main_fragment = 'main.{0}.xhtml'.format(article_doi) + '#{0}'
        self.biblio_fragment = 'biblio.{0}.xhtml'.format(article_doi) + '#{0}'
        self.tables_fragment = 'tables.{0}.xhtml'.format(article_doi) + '#{0}'

        self.epub2_support = False
        self.epub3_support = False
        self.epub_default = 2
        self.epub2_maker_methods = self.maker2.all
        self.epub3_maker_methods = self.maker3.all
        self.epub2_special_methods = self.special2.all
        self.epub3_special_methods = self.special3.all

    @property
    def article(self):
        return self._article()

    @article.setter
    def article(self, article_instance):
        self._article = weakref.ref(article_instance)

    def doi_prefix(self):
        return self.article.doi.split('/')[0]

    def doi_suffix(self):
        return self.article.doi.split('/', 1)[1]

    def post_process(self, document, epub_version):
        def recursive_traverse(element):

            try:
                tag_method = getattr(self,
                                     'process_{0}_tag'.format(element.tag.replace('-', '_')),
                                     None)
            except AttributeError:
                if element is None:
                    return
                if isinstance(element, etree._Comment):
                    log.warning('''Comment encountered during recursive \
post-processing, removing it''')
                    remove(element)
                    return
            if tag_method is not None and callable(tag_method):
                tag_method(element, epub_version)
            for subel in element:
                recursive_traverse(subel)

        body = document.getroot().find('body')
        recursive_traverse(body)

    def make_document(self, titlestring):
        """
        This method may be used to create a new document for writing as xml
        to the OPS subdirectory of the ePub structure.
        """
        #root = etree.XML('''<?xml version="1.0"?>\
#<!DOCTYPE html  PUBLIC '-//W3C//DTD XHTML 1.1//EN'  'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'>\
#<html xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml" xmlns:ops="http://www.idpf.org/2007/ops">\
#</html>''')

        root = etree.XML('''<?xml version="1.0"?>\
<!DOCTYPE html>\
<html xmlns="http://www.w3.org/1999/xhtml">\
</html>''')

        document = etree.ElementTree(root)
        html = document.getroot()
        head = etree.SubElement(html, 'head')
        etree.SubElement(html, 'body')
        title = etree.SubElement(head, 'title')
        title.text = titlestring
        #The href for the css stylesheet is a standin, can be overwritten
        etree.SubElement(head,
                         'link',
                         {'href': 'css/default.css',
                          'rel': 'stylesheet',
                          'type': 'text/css'})

        return document

    def render_content(self, output_directory, epub_version=None):
        if epub_version is None:
            epub_version = self.epub_default
        self.main = self.make_document('main')
        self.biblio = self.make_document('biblio')
        self.tables = self.make_document('tables')

        #Copy over the article's body
        if self.article.body is not None:
            replace(self.main.getroot().find('body'),
                    deepcopy(self.article.body))

        if int(epub_version) == 2:
            if not self.epub2_support:
                log.error('EPUB2 not supported by this publisher')
                raise NotImplementedError('EPUB2 is not supported')
            else:
                for func in self.epub2_maker_methods:
                    self.__getattribute__(func.__name__)()
                for func in self.epub2_special_methods:
                    self.__getattribute__(func.__name__)()
        elif int(epub_version) == 3:
            if not self.epub3_support:
                log.error('EPUB3 not supported by this publisher')
                raise NotImplementedError('EPUB3 is not supported')
            else:
                for func in self.epub3_maker_methods:
                    self.__getattribute__(func.__name__)()
                for func in self.epub3_special_methods:
                    self.__getattribute__(func.__name__)()
        else:
            log.error('Improper EPUB version specified')
            raise ValueError('epub_version should be 2 or 3')

        #Conduct post-processing on all documents and write them
        self.post_process(self.main, epub_version)
        self.depth_headings(self.main)
        self.write_document(self.main_filename(output_directory), self.main)

        for fn, doc in [(self.biblio_filename(output_directory), self.biblio),
                        (self.tables_filename(output_directory), self.tables)]:
            if len(doc.getroot().find('body')) == 0:
                continue
            self.post_process(doc, epub_version)
            self.write_document(fn, doc)

    def main_filename(self, output_directory):
        return os.path.join(output_directory, 'EPUB', self.main_fragment[:-4])

    def biblio_filename(self, output_directory):
        return os.path.join(output_directory, 'EPUB', self.biblio_fragment[:-4])

    def tables_filename(self, output_directory):
        return os.path.join(output_directory, 'EPUB', self.tables_fragment[:-4])

    def write_document(self, name, document):
        """
        This function will write a document to an XML file.
        """
        with open(name, 'wb') as out:
            out.write(etree.tostring(document,
                                     encoding='utf-8',
                                     pretty_print=True))

    def nav_contributors(self):
        """
        Returns a list of contributors to the article.

        This is a metadata method that is only required to be defined for
        EPUB2 creation, though the `package_contributors` counterpart should
        always be present. This method returns a list of special namedtuples
        with the following specification: Contributor(name, role, file_as).
        The 'name' should be a string representing a standard reading form of
        the contributor's name. The 'role' will indicate one of the following:
        'author', 'editor', and 'reviewer'. The 'file_as' will be a string
        representing a name as it would be catalogued. This method may differ
        from `package_contributors` if one desires, but it covers extra details
        so that it they can easily be the same.

        Returns
        -------
        list of Contributor namedtuples
            A list of contributors, [Contributor(name, role, file_as)].

        Notes
        -----
        The Navigation Document will utilize the results of this method in the
        following manner: When making EPUB2, if Contributor.role is 'author',
        then Contributor.name will be entered as a docAuthor.
        """
        raise NotImplementedError

    def nav_title(self):
        """
        Returns a string for the title of the article.

        This is a required metadata method used for representing the article's
        title in the Navigation Document of the EPUB. It simply returns a string
        of the title's text. It may differ from `package_title` but it is also
        likely that these methods may be the same, in which case one may use a
        strategy to ensure they return the same results.

        Returns
        -------
        str
            The `title` of the article being parsed for metadata.

        Notes
        -----
        This method is likely to benefit from the `serialize` method in the
        `openaccess_epub.utils.element_methods` module.
        """
        raise NotImplementedError

    def package_identifier(self):
        """
        Returns an identifier for the article.

        This is a required metadata method used for representing a unique
        identifier for the article. Typically this will simply be the article's
        DOI. The namedtuple which this method returns is of the form
        Identifier(value, scheme).

        Returns
        -------
        Identifier namedtuple
            A single Identifier(value, scheme).
        """
        raise NotImplementedError

    def package_language(self):
        """
        Returns a list of language tags indicating languages used in the
        article.

        This is a required metadata method used to indicate the languages in
        which the content of the article is written. This method returns a list
        of string language codes (which must conform to
        http://tools.ietf.org/html/rfc5646).

        Returns
        -------
        list of str
            A list of strings conforming to language codes.
        """
        raise NotImplementedError

    def package_title(self):
        """
        Returns a string for the title of the article.

        This is a required metadata method used for representing the article's
        title in the Package Document of the EPUB. It simply returns a string
        of the title's text. It may differ from `nav_title` but it is also
        likely that these methods may be the same, in which case one may use a
        strategy to ensure they return the same results.

        Returns
        -------
        str
            The `title` of the article being parsed for metadata.

        Notes
        -----
        This method is likely to benefit from the `serialize` method in the
        `openaccess_epub.utils.element_methods` module.
        """
        raise NotImplementedError

    #TODO: Implement alternate-language scripts for contributors
    def package_contributors(self):
        """
        Returns a list of contributors to the article.

        This method returns a list of special namedtuples representing
        contributors to the article. These follow the follow specification:
        Contributor(name, role, file_as). The 'name' should be a string
        representing a standard reading form of the contributor's name. The
        'role' should be a MARC relator value (see References).
        The 'file_as' will be a string representing a name as it
        would be catalogued. This method may differ from `nav_contributors`
        if one desires, but they generally overlap.

        Returns
        -------
        list of Contributor namedtuples
            A list of contributors, [Contributor(name, role, file_as)].

        Notes
        -----
        Appropriate entries for authors and editors will be created in the
        Packaging Document using the data returned by this method.

        References
        ----------
        http://www.loc.gov/marc/relators/relaterm.html
        http://www.loc.gov/marc/relators/relacode.html
        """
        raise NotImplementedError

    def package_subject(self):
        """
        Returns a list of strings representing keyword subjects relevant to the
        article's content.

        This is an optional metadata method representing keyword subjects
        covered in the article's content. Each string returned in the list will
        be added to the Package Document metadata as a keyword.

        Returns
        -------
        list of str
            List of keyword strings representing content subjects.
        """
        return []

    def package_publisher(self):
        """
        Returns the full name of the publsher as it should be written in the
        Package Document metadata.

        This is an optional metadata method for entering the publisher's name
        in the Package Document metadata. This is super simple, just return a
        string for your publisher name.

        Returns
        -------
        str
            Name of the publisher.
        """
        return ''

    def package_description(self):
        """
        Returns a string description of the article. This may be the serialized
        text of the abstract.

        This is an optional metadata method for entering a description of the
        article in the Package Document metadata. In many cases, the description
        may be best provided by the article's abstract if it has one. This
        returns a string of plain text, though the abstract may commonly include
        nested XML elements; serializing the abstract should be employed.

        Returns
        -------
        str or None
            Description of the article. None if no description available.
        """
        return None

    def package_date(self):
        """
        Returns a list of important dates for the article.

        This is an optional metadata method which may be used to make entries
        for important dates in the Package Document metadata. This method
        returns a list of special Date namedtuples which are of the form:
        Date(year, month, day, event). The event value should be one of
        'accepted', 'copyrighted', 'submitted', None if not used.

        Returns
        -------
        list of Date namedtuples
            A list of dates, [Date(year, month, day, event)].
        """
        return []

    def package_rights(self):
        """
        Returns a string representing a copyright statement for the article.

        This is a requied metadata method which will be used to provide an
        appropriate statement of rights in the Package Document. This method
        should return a string.

        Returns
        -------
        str
            A string for the copyright statement of the article.

        Notes
        -----
        Elegantly handling rights from multiple works within the Package
        Document may be a challenge but very important. Constructive feedback is
        highly welcome at all times to attempt to follow best practices. I will
        review aspects of this challenge, as well as summarize how the Package
        Document handles it.

        Most OA articles are published under a variant of the Creative Commons
        license, and different versions of this license retain differ in terms
        or rights and restrictions. Due to the fact that articles may be
        published under different licenses, care should be taken to ensure that
        clear notice is given to the licensing of individual articles and that
        incompatible licenses are not mixed.

        Creating an EPUB of an article (or compiling them in a collection) is
        considered the creation of a derivative work; the EPUB should not be
        considered a verbatim copy of the work. Licenses which do not allow
        derivative works are not compatible with OpenAccess_EPUB. Likewise, the
        use of OpenAccess_EPUB to create content for commercial purposes is
        not compatible with licenses that prohibit commercial use. It is not the
        responsibility of OpenAccess_EPUB (an open source, freely available and
        modifiable software) to enforce conformance to licensing rules.

        If all articles in a collection are published according to the same
        license, a rights entry will be made in the Package Document displaying
        that license along with a note that it pertains to all articles. If
        there are multiple licenses in the collection, a rights entry will be
        created which details each individual license, along with the distinct
        articles to which they pertain.
        """
        return NotImplementedError

    def format_date_string(self, date_tuple):
        """
        Receives a date_tuple object, and outputs a string
        for placement in the article content.
        """
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        date_string = ''
        if date_tuple.season:
            return '{0}, {1}'.format(date_tuple.season, date_tuple.year)
        else:
            if not date_tuple.month and not date_tuple.day:
                return '{0}'.format(date_tuple.year)
            if date_tuple.month:
                date_string += months[int(date_tuple.month)]
            if date_tuple.day:
                date_string += ' ' + date_tuple.day
            return ', '.join([date_string, date_tuple.year])

    #These methods are recognized as Post Processing methods, as a final step in
    #the rendering of documents, the tree is recursively traversed. During this
    #traversal each element's tag is read, let's say some tag is 'X'. If there
    #exists a method called 'process_X_tag', that method will be called before
    #continuing the traversal; if the method does not exist, the traversal will
    #simply continue. Tag names may contain hyphens, '-', while method names may
    #not. These will be coerced to '_' for lookup (tag 'sans-serif' will match
    #method 'process_sans_serif_tag').
    #
    #Post Processing methods *should not* modify other elements in the element
    #tree, as this may perturb the traversal. These methods *may* remove the
    #element on which they act from the tree.
    #
    #All Post Processing methods accept the arguments:
    #(self, element, epub_version)
    #epub_version is an integer, 2 or 3, and should be used to control
    #unique behavior between versions.
    def process_bold_tag(self, element, epub_version):
        element.tag = 'b'

    def process_italic_tag(self, element, epub_version):
        element.tag = 'i'

    def process_monospace_tag(self, element, epub_version):
        if epub_version == 2:
            element.tag = 'span'
            element.attrib['style'] = 'font-family:monospace'
        #This is here for demonstration, it may be discarded later
        elif epub_version == 3:
            element.tag = 'code'

    def process_overline_tag(self, element, epub_version):
        element.tag = 'span'
        element.attrib['style'] = 'text-decoration:overline'

    def process_sans_serif_tag(self, element, epub_version):
        element.tag = 'span'
        element.attrib['style'] = 'font-family:sans-serif'

    def process_sc_tag(self, element, epub_version):
        element.tag = 'span'
        element.attrib['style'] = 'font-variant:small-caps'

    def process_strike_tag(self, element, epub_version):
        element.tag = 'span'
        element.attrib['style'] = 'text-decoration:line-through'

    def process_underline_tag(self, element, epub_version):
        element.tag = 'span'
        element.attrib['style'] = 'text-decoration:underline'

    def process_email_tag(self, element, epub_version):
        remove_all_attributes(element)
        element.tag = 'a'
        element.attrib['href'] = 'mailto:' + element.text

    def process_ext_link_tag(self, element, epub_version):
        element.tag = 'a'
        xlink_href_name = ns_format(element, 'xlink:href')
        xlink_href = element.attrib.get(xlink_href_name)
        remove_all_attributes(element)
        if xlink_href is None:
            element.attrib['href'] = element_methods.all_text(element)
        else:
            element.attrib['href'] = xlink_href

    def process_xref_tag(self, element, epub_version):
        #TODO: Consider creating an xref_ref_type_map instance variable instead
        #of defining it in this method. It might allow for useful customization
        ref_map = {'bibr': self.biblio_fragment,
                   'fig': self.main_fragment,
                   'supplementary-material': self.main_fragment,
                   'table': self.main_fragment,
                   'aff': self.main_fragment,
                   'sec': self.main_fragment,
                   'table-fn': self.tables_fragment,
                   'boxed-text': self.main_fragment,
                   'other': self.main_fragment,
                   'disp-formula': self.main_fragment,
                   'fn': self.main_fragment,
                   'app': self.main_fragment,
                   None: self.main_fragment}

        element.tag = 'a'
        ref_type = element.attrib.get('ref-type')
        rid = element.attrib['rid']  # What good is an xref without 'rid'
        remove_all_attributes(element)
        reference = ref_map[ref_type].format(rid)
        element.attrib['href'] = reference

    def process_sec_tag(self, element, epub_version):
        element.tag = 'div'
        rename_attributes(element, {'sec-type': 'class'})

    def depth_headings(self, document):
        depth_tags = ['h2', 'h3', 'h4', 'h5', 'h6']

        def recursive_traverse(element, depth=0):
            for div in element.findall('div'):
                label = div.find('label')
                title = div.find('title')
                if label is not None:
                    #If there is a label, but it is empty
                    if len(label) == 0 and label.text is None:
                        remove(label)
                        label = None
                if title is not None:
                    #If there is a title, but it is empty
                    if len(title) == 0 and title.text is None:
                        remove(title)
                        title = None
                if label is not None:
                    label.tag = 'b'
                if title is not None:
                    if depth < len(depth_tags):
                        title.tag = depth_tags[depth]
                    else:
                        title.tag = 'span'
                        title.attrib['class'] = 'extendedheader' + str(depth)
                    if label is not None:
                        #If the label exists, prepend its text then remove it
                        title.text = ' '.join([label.text, title.text])
                        remove(label)
                recursive_traverse(div, depth=depth + 1)

        body = document.getroot().find('body')
        recursive_traverse(body, depth=1)

    def has_out_of_flow_tables(self):
        """
        Returns True if the article has out-of-flow tables, indicates separate
        tables document.

        This method is used to indicate whether rendering this article's content
        will result in the creation of out-of-flow HTML tables. This method has
        a base class implementation representing a common logic; if an article
        has a graphic(image) representation of a table then the HTML
        representation will be placed out-of-flow if it exists, if there is no
        graphic(image) represenation then the HTML representation will be placed
        in-flow.

        Returns
        -------
        bool
            True if there are out-of-flow HTML tables, False otherwise
        """
        if self.article.body is None:
            return False
        for table_wrap in self.article.body.findall('.//table-wrap'):
            graphic = table_wrap.xpath('./graphic | ./alternatives/graphic')
            table = table_wrap.xpath('./table | ./alternatives/table')
            if graphic and table:
                return True
        return False
