# -*- coding: utf-8 -*-
"""
Common utility functions
"""
import os.path
import zipfile
from collections import namedtuple
import urllib
import logging
import time
import shutil
import re
import sys

from openaccess_epub.utils.css import DEFAULT_CSS
from openaccess_epub.utils.input import doi_input, url_input

#Python documentation refers to this recipe for an OrderedSet
#http://code.activestate.com/recipes/576694/
import collections

class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = [] 
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:        
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

def cache_location():
    '''Cross-platform placement of cached files'''
    if sys.platform == 'win32':  # Windows
        return os.path.join(os.environ['APPDATA'], 'OpenAccess_EPUB')
    else:  # Mac or Linux
        path = os.path.expanduser('~')
        if path == '~':
            path = os.path.expanduser('~user')
            if path == '~user':
                sys.exit('Could not find the correct cache location')
        return os.path.join(path, '.OpenAccess_EPUB')

log = logging.getLogger('utils')

Identifier = namedtuple('Identifer', 'id, type')


def mkdir_p(dir):
    if os.path.isdir(dir):
        return
    os.makedirs(dir)

def evaluate_relative_path(working=os.getcwd(), relative=''):
    """
    This function receives two strings representing system paths. The first is
    the working directory and it should be an absolute path. The second is the
    relative path and it should not be absolute. This function will render an
    OS-appropriate absolute path, which is the normalized path from working
    to relative.
    """
    return os.path.normpath(os.path.join(working, relative))


def get_absolute_path(some_path):
    """
    This function will return an appropriate absolute path for the path it is
    given. If the input is absolute, it will return unmodified; if the input is
    relative, it will be rendered as relative to the current working directory.
    """
    if os.path.isabs(some_path):
        return some_path
    else:
        return evaluate_relative_path(os.getcwd(), some_path)


def get_output_directory(args):
    """
    Determination of the directory for output placement involves possibilities
    for explicit user instruction (absolute path or relative to execution) and
    implicit default configuration (absolute path or relative to input) from
    the system global configuration file. This function is responsible for
    reliably returning the appropriate output directory which will contain any
    log(s), ePub(s), and unzipped output of OpenAccess_EPUB.

    It utilizes the parsed args, passed as an object, and is self-sufficient in
    accessing the config file.

    All paths returned by this function are absolute.
    """
    #Import the global config file as a module
    import imp
    config_path = os.path.join(cache_location(), 'config.py')
    try:
        config = imp.load_source('config', config_path)
    except IOError:
        print('Could not find {0}, please run oae-quickstart'.format(config_path))
        sys.exit()
    #args.output is the explicit user instruction, None if unspecified
    if args.output:
        #args.output may be an absolute path
        if os.path.isabs(args.output):
            return args.output  # return as is
        #or args.output may be a relative path, relative to cwd
        else:
            return evaluate_relative_path(relative=args.output)
    #config.default_output for default behavior without explicit instruction
    else:
        #config.default_output may be an absolute_path
        if os.path.isabs(config.default_output):
            return config.default_output
        #or config.default_output may be a relative path, relative to input
        else:
            if args.input:  # The case of single input
                if 'http://www' in args.input:
                    #Fetched from internet by URL
                    raw_name = url_input(args.input, download=False)
                    abs_input_path = os.path.join(os.getcwd(), raw_name+'.xml')
                elif args.input[:4] == 'doi:':
                    #Fetched from internet by DOI
                    raw_name = doi_input(args.input, download=False)
                    abs_input_path = os.path.join(os.getcwd(), raw_name+'.xml')
                else:
                    #Local option, could be anywhere
                    abs_input_path = get_absolute_path(args.input)
                abs_input_parent = os.path.split(abs_input_path)[0]
                return evaluate_relative_path(abs_input_parent, config.default_output)
            elif args.batch:  # The case of Batch Mode
                #Batch should only work on a supplied directory
                abs_batch_path = get_absolute_path(args.batch)
                return abs_batch_path
            elif args.parallel_batch:
                #Batch should only work on a supplied directory
                abs_batch_path = get_absolute_path(args.parallel_batch)
                return abs_batch_path
            elif args.collection:
                return os.getcwd()
            else:  # Un-handled or currently unsupported options
                print('The output location could not be determined...')
                sys.exit()


def getFileRoot(path):
    """
    This method provides a standard method for acquiring the root name of a
    file from a path string. It will not raise an error if it returns an empty
    string, but it will issue a warning.
    """
    bn = os.path.basename(path)
    root = os.path.splitext(bn)[0]
    if not root:
        w = 'getFileRoot could not derive a root file name from\"{0}\"'
        log.warning(w.format(path))
        print(w.format(path))
    return root



def make_epub_base():
    """
    Contains the  functionality to create the ePub directory hierarchy from
    scratch. Typical practice will not require this method, but use this to
    replace the default base ePub directory if it is not present. It may also
    used as a primer on ePub directory construction:
    base_epub/
    base_epub/mimetype
    base_epub/META-INF/
    base_epub/META-INF/container.xml
    base_epub/OPS/
    base_epub/OPS/css
    base_epub/OPS/css/article.css
    """
    location = os.path.join(cache_location(), 'base_epub')
    if os.path.isdir(location):
        return
    log.info('Making the ePub base at {0}'.format(location))
    mkdir_p(location)
    #Create mimetype file in root directory
    mime_path = os.path.join(location, 'mimetype')
    with open(mime_path, 'w') as mimetype:
        mimetype.write('application/epub+zip')
    #Create OPS and META-INF directorys
    os.mkdir(os.path.join(location, 'META-INF'))
    os.mkdir(os.path.join(location, 'OPS'))
    #Create container.xml file in META-INF
    meta_path = os.path.join(location, 'META-INF', 'container.xml')
    with open(meta_path, 'w') as container:
        container.write('''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>''')
    #It is considered better practice to leave the instantiation of image
    #directories up to other methods. Such directories are technically
    #optional and may depend on content
    #Create the css directory in OPS, then copy the file from resources
    os.mkdir(os.path.join(location, 'OPS', 'css'))
    css_path = os.path.join(location, 'OPS', 'css', 'article.css')
    with open(css_path, 'wb') as css:
        css.write(bytes(DEFAULT_CSS, 'UTF-8'))

def createDCElement(document, name, data, attributes = None):
    """
    A convenience method for creating DC tag elements.
    Used in content.opf
    """
    newnode = document.createElement(name)
    newnode.appendChild(document.createTextNode(data))
    if attributes:
        for attr, attrval in attributes.iteritems():
            newnode.setAttribute(attr, attrval)
    return newnode


def stripDOMLayer(oldnodelist, depth=1):
    """
    This method strips layers \"off the top\" from a specified NodeList or
    Node in the DOM. All child Nodes below the stripped layers are returned as
    a NodeList, treating them as siblings irrespective of the original
    hierarchy. To be used with caution.
    """
    newnodelist = []
    while depth:
        try:
            for child in oldnodelist:
                newnodelist += child.childNodes
        except TypeError:
            newnodelist = oldnodelist.childNodes
        depth -= 1
        newnodelist = stripDOMLayer(newnodelist, depth)
        return newnodelist
    return oldnodelist


def serializeText(fromnode, stringlist=None, sep=''):
    """
    Recursively extract the text data from a node and it's children
    """
    if stringlist is None:
        stringlist = []
    for item in fromnode.childNodes:
        if item.nodeType == item.TEXT_NODE and not item.data == '\n':
            stringlist.append(item.data)
        else:
            serializeText(item, stringlist, sep)
    return sep.join(stringlist)


#I wish to eventually shift all serializeText references to serialize_text
def serialize_text(fromnode, stringlist=None, sep=''):
    """
    Recursively extract the text data from a node and it's children
    """
    if stringlist is None:
        stringlist = []
    for item in fromnode.childNodes:
        if item.nodeType == item.TEXT_NODE and not item.data == '\n':
            stringlist.append(item.data)
        else:
            serializeText(item, stringlist, sep)
    return sep.join(stringlist)


def nodeText(node):
    """
    This is to be used when a node may only contain text, numbers or special
    characters. This function will return the text contained in the node.
    Sometimes this text data contains spurious newlines and spaces due to
    parsing and original xml formatting. This function should strip such
    artifacts.
    """
    #Get data from first child of the node
    try:
        first_child_data = node.firstChild.data
    except AttributeError:  # Usually caused by an empty node
        return ''
    else:
        return '{0}'.format(first_child_data.strip())


def getTagData(node_list):
    '''Grab the (string) data from text elements
    node_list -- NodeList returned by getElementsByTagName
    '''
    data = ''
    try:
        for node in node_list:
            if node.firstChild.nodeType == node.TEXT_NODE:
                data = node.firstChild.data
        return data
    except TypeError:
        getTagData([node_list])


def getTagText(node):
    """
    Grab the text data from a Node. If it is provided a NodeList, it will
    return the text data from the first contained Node.
    """
    data = ''
    try:
        children = node.childNodes
    except AttributeError:
        getTagText(node[0])
    else:
        if children:
            for child in children:
                if child.nodeType == child.TEXT_NODE and child.data != '\n':
                    data += child.data
            return data


def getFormattedNode(node):
    """
    This method is called on a Node whose children may include emphasis
    elements. The contained emphasis elements will be converted to ePub-safe
    emphasis elements. Non-emphasis elements will be untouched.
    """
    #Some of these elements are to be supported through CSS
    emphasis_elements = ['bold', 'italic', 'monospace', 'overline',
                         'sc', 'strike', 'underline']
    spans = {'monospace': 'font-family:monospace',
             'overline': 'text-decoration:overline',
             'sc': 'font-variant:small-caps',
             'strike': 'text-decoration:line-through',
             'underline': 'text-decoration:underline'}

    clone = node.cloneNode(deep=True)
    for element in emphasis_elements:
        for item in clone.getElementsByTagName(element):
            if item.tagName == 'bold':
                item.tagName = 'b'
            elif item.tagName == 'italic':
                item.tagName = 'i'
            elif item in spans:
                item.tagName = 'span'
                item.setAttribute('style', spans[item])
    return clone


def epub_zip(outdirect):
    """Zips up the input file directory into an ePub file."""
    log.info('Zipping up the directory {0}'.format(outdirect))
    epub_filename = outdirect + '.epub'
    epub = zipfile.ZipFile(epub_filename, 'w')
    current_dir = os.getcwd()
    os.chdir(outdirect)
    epub.write('mimetype')
    log.info('Recursively zipping META-INF and OPS')
    recursive_zip(epub, 'META-INF')
    recursive_zip(epub, 'OPS')
    os.chdir(current_dir)
    epub.close()


def recursive_zip(zipf, directory, folder=''):
    """Recursively traverses the output directory to construct the zipfile"""
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), os.path.join(directory,
                                                                   item))
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(zipf, os.path.join(directory, item),
                          os.path.join(folder, item))


suggested_article_types = ['abstract', 'addendum', 'announcement',
    'article-commentary','book-review', 'books-received', 'brief-report',
    'calendar', 'case-report', 'collection', 'correction', 'discussion',
    'dissertation', 'editorial', 'in-brief', 'introduction', 'letter',
    'meeting-report', 'news', 'obituary', 'oration', 'partial-retraction',
    'product-review', 'rapid-communication', 'rapid-communication', 'reply',
    'reprint', 'research-article', 'retraction', 'review-article',
    'translation']


def initiateDocument(titlestring,
                     _publicId='-//W3C//DTD XHTML 1.1//EN',
                     _systemId='http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'):
    """A method for conveniently initiating a new xml.DOM Document"""
    from xml.dom.minidom import getDOMImplementation

    impl = getDOMImplementation()

    mytype = impl.createDocumentType('article', _publicId, _systemId)
    doc = impl.createDocument(None, 'root', mytype)

    root = doc.lastChild #IGNORE:E1101
    root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
    root.setAttribute('xml:lang', 'en-US')

    head = doc.createElement('head')
    root.appendChild(head)

    title = doc.createElement('title')
    title.appendChild(doc.createTextNode(titlestring))

    link = doc.createElement('link')
    link.setAttribute('rel', 'stylesheet')
    link.setAttribute('href','css/reference.css')
    link.setAttribute('type', 'text/css')

    meta = doc.createElement('meta')
    meta.setAttribute('http-equiv', 'Content-Type')
    meta.setAttribute('content', 'application/xhtml+xml')
    meta.setAttribute('charset', 'utf-8')

    headlist = [title, link, meta]
    for tag in headlist:
        head.appendChild(tag)
    root.appendChild(head)

    body = doc.createElement('body')
    root.appendChild(body)

    return doc, body


def plos_fetch_single_representation(article_doi, item_xlink_href):
    """
    This function will render a formatted URL for accessing the PLoS' server
    SingleRepresentation of an object.
    """
    #A dict of URLs for PLoS subjournals
    journal_urls = {'pgen': 'http://www.plosgenetics.org/article/{0}',
                    'pcbi': 'http://www.ploscompbiol.org/article/{0}',
                    'ppat': 'http://www.plospathogens.org/article/{0}',
                    'pntd': 'http://www.plosntds.org/article/{0}',
                    'pmed': 'http://www.plosmedicine.org/article/{0}',
                    'pbio': 'http://www.plosbiology.org/article/{0}',
                    'pone': 'http://www.plosone.org/article/{0}',
                    'pctr': 'http://clinicaltrials.ploshubs.org/article/{0}'}
    #Identify subjournal name for base URl
    subjournal_name = article_doi.split('.')[1]
    base_url = journal_urls[subjournal_name]

    #Compose the address for fetchSingleRepresentation
    resource = 'fetchSingleRepresentation.action?uri=' + item_xlink_href
    return base_url.format(resource)


def scrapePLoSIssueCollection(issue_url):
    """
    Uses Beautiful Soup to scrape the PLoS page of an issue. It is used
    instead of xml.dom.minidom because of malformed html/xml
    """
    iu = urllib.urlopen(issue_url)
    with open('temp','w') as temp:
        temp.write(iu.read())
    with open('temp', 'r') as temp:
        soup = BeautifulStoneSoup(temp)
    os.remove('temp')
    #Map the journal urls to nice strings
    jrns = {'plosgenetics': 'PLoS_Genetics', 'plosone': 'PLoS_ONE',
            'plosntds': 'PLoS_Neglected_Tropical_Diseases', 'plosmedicine':
            'PLoS_Medicine', 'plosbiology': 'PLoS_Biology', 'ploscompbiol':
            'PLoS_Computational_Biology', 'plospathogens': 'PLoS_Pathogens'}
    toc = soup.find('h1').string
    date = toc.split('Table of Contents | ')[1].replace(' ', '_')
    key = issue_url.split('http://www.')[1].split('.org')[0]
    name = '{0}_{1}.txt'.format(jrns[key], date)
    collection_name = os.path.join('collections', name)
    with open(collection_name, 'w') as collection:
        links = soup.findAll('a', attrs={'title': 'Read Open Access Article'})
        for link in links:
            href = link['href']
            if href[:9] == '/article/':
                id = href.split('10.1371%2F')[1].split(';')[0]
                collection.write('doi:10.1371/{0}\n'.format(id))
