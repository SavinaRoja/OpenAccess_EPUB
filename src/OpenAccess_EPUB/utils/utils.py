"""
Common utility functions
"""
import os.path
import zipfile
from collections import namedtuple
import urllib2
import shutil
import time
import re
import logging

log = logging.getLogger('utils')

Identifier = namedtuple('Identifer', 'id, type')


def nodeText(node):
    """
    This is to be used when a node may only contain text, numbers or special
    characters. This function will return the text contained in the node.
    Sometimes this text data contains spurious newlines and spaces due to
    parsing and original xml formatting. This function should strip such
    artifacts.
    """
    return u'{0}'.format(node.firstChild.data.strip())


def makeEPUBBase(location):
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
    base_epub/OPS/images/
    base_epub/OPS/images/equations/
    base_epub/OPS/images/figures/
    base_epub/OPS/images/tables/
    """
    log.info('Making the Base ePub at {0}'.format(location))
    #Create root directory
    os.mkdir(location)
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
    with open(css_path, 'w') as css:
        log.info('Fetching a filler CSS file from GitHub')
        dl_css = urllib2.urlopen('https://github.com/downloads/SavinaRoja/OpenAccess_EPUB/text.css')
        css.write(dl_css.read())


def buildCache(location):
    log.info('Building the cache at {0}'.format(location))
    os.mkdir(location)
    os.mkdir(os.path.join(location, 'img_cache'))
    os.mkdir(os.path.join(location, 'logs'))
    os.mkdir(os.path.join(location, 'downloaded_xml_files'))
    os.mkdir(os.path.join(location, 'css'))
    os.mkdir(os.path.join(location, 'output'))
    makeEPUBBase(location)


def initImgCache(img_cache):
    """
    Initiates the image cache if it does not exist
    """
    log.info('Initiating the image cache at {0}'.format(img_cache))
    os.mkdir(img_cache)
    os.mkdir(os.path.join(img_cache, 'model'))
    os.mkdir(os.path.join(img_cache, 'PLoS'))
    os.mkdir(os.path.join(img_cache, 'Frontiers'))
    os.mkdir(os.path.join(img_cache, 'model', 'images'))


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


def serializeText(fromnode, stringlist=[], sep=u''):
    """
    Recursively extract the text data from a node and it's children
    """
    for item in fromnode.childNodes:
        if item.nodeType == item.TEXT_NODE and not item.data == u'\n':
            stringlist.append(item.data)
        else:
            serializeText(item, stringlist, sep)
    return sep.join(stringlist)


def getTagText(node):
    """
    Grab the text data from a Node. If it is provided a NodeList, it will
    return the text data from the first contained Node.
    """
    data = u''
    try:
        children = node.childNodes
    except AttributeError:
        getTagText(node[0])
    else:
        if children:
            for child in children:
                if child.nodeType == child.TEXT_NODE and child.data != u'\n':
                    data = child.data
            return data


def getFormattedNode(node):
    """
    This method is called on a Node whose children may include emphasis
    elements. The contained emphasis elements will be converted to ePub-safe
    emphasis elements. Non-emphasis elements will be untouched.
    """
    #Some of these elements are to be supported through CSS
    emphasis_elements = [u'bold', u'italic', u'monospace', u'overline',
                         u'sc', u'strike', u'underline']
    spans = {u'monospace': u'font-family:monospace',
             u'overline': u'text-decoration:overline',
             u'sc': u'font-variant:small-caps',
             u'strike': u'text-decoration:line-through',
             u'underline': u'text-decoration:underline'}

    clone = node.cloneNode(deep=True)
    for element in emphasis_elements:
        for item in clone.getElementsByTagName(element):
            if item.tagName == u'bold':
                item.tagName = u'b'
            elif item.tagName == u'italic':
                item.tagName = u'i'
            elif item in spans:
                item.tagName = u'span'
                item.setAttribute('style', spans[item])
    return clone


def getTagData(node_list):
    '''Grab the (string) data from text elements
    node_list -- NodeList returned by getElementsByTagName
    '''
    data = u''
    try:
        for node in node_list:
            if node.firstChild.nodeType == node.TEXT_NODE:
                data = node.firstChild.data
        return data
    except TypeError:
        getTagData([node_list])


def epubZip(outdirect):
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


def suggestedArticleTypes():
    """
    Returns a list of suggested values for article-type
    """
    #See http://dtd.nlm.nih.gov/publishing/tag-library/3.0/n-w2d0.html
    s = ['abstract', 'addendum', 'announcement', 'article-commentary',
         'book-review', 'books-received', 'brief-report', 'calendar',
         'case-report', 'collection', 'correction', 'discussion',
         'dissertation', 'editorial', 'in-brief', 'introduction', 'letter',
         'meeting-report', 'news', 'obituary', 'oration',
         'partial-retraction', 'product-review', 'rapid-communication',
         'rapid-communication', 'reply', 'reprint', 'research-article',
         'retraction', 'review-article', 'translation']
    return(s)


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


def scrapePLoSIssueCollection(issue_url):
    """
    Uses Beautiful Soup to scrape the PLoS page of an issue. It is used
    instead of xml.dom.minidom because of malformed html/xml
    """
    iu = urllib2.urlopen(issue_url)
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


def fetchFrontiersImages(doi, counts, cache_dir, output_dir, caching):
    """
    Using the power of web-scraping and, we will get the images from the
    Frontiers pages. If run locally by Frontiers staffpersons, this method
    should be avoidable.
    """
    log.info('Fetching Frontiers images')

    def downloadImage(fetch, img_file):
        try:
            image = urllib2.urlopen(fetch)
        except urllib2.HTTPError, e:
            if e.code == 503:  # Server overloaded
                time.sleep(1)  # Wait one second
                try:
                    image = urllib2.urlopen(fetch)
                except:
                    return None
            elif e.code == 500:
                print('urllib2.HTTPError {0}'.format(e.code))
            return None
        else:
            with open(img_file, 'wb') as outimage:
                outimage.write(image.read())
        return True

    def checkEquationCompletion(images):
        """
        In some cases, equations images are not exposed in the fulltext (hidden
        behind a rasterized table). This attempts to look for gaps and fix them
        """
        log.info('Checking for complete equations')
        files = os.listdir(img_dir)
        inline_equations = []
        for e in files:
            if e[0] == 'i':
                inline_equations.append(e)
        missing = []
        highest = 0
        if inline_equations:
            inline_equations.sort()
            highest = int(inline_equations[-1][1:4])
            i = 1
            while i < highest:
                name = 'i{0}.gif'.format(str(i).zfill(3))
                if name not in inline_equations:
                    missing.append(name)
                i += 1
        get = images[0][:-8]
        for m in missing:
            loc = os.path.join(img_dir, 'equations', m)
            downloadImage(get + m, loc)
            print('Downloaded image {0}'.format(loc))
        #It is possible that we need to go further than the highest
        highest += 1
        name = 'i{0}.gif'.format(str(highest).zfill(3))
        loc = os.path.join(img_dir, 'equations', name)
        while downloadImage(get + name, loc):
            print('Downloaded image {0}'.format(loc))
            highest += 1
            name = 'i{0}.gif'.format(str(highest).zfill(3))

    print('Processing images for {0}...'.format(doi))
    s = os.path.split(doi)[1]
    img_dir = os.path.join(output_dir, 'OPS', 'images-{0}'.format(s))
    #Check to see if this article's images have been cached
    art_cache = os.path.join(cache_dir, 'Frontiers', s)
    art_cache_images = os.path.join(art_cache, 'images')
    if os.path.isdir(art_cache):
        print('Cached images found. Transferring from cache...')
        shutil.copytree(art_cache_images, img_dir)
        return None
    else:
        model_images = os.path.join(cache_dir, 'model', 'images')
        shutil.copytree(model_images, img_dir)
        #We use the DOI of the article to locate the page.
        doistr = 'http://dx.doi.org/{0}'.format(doi)
        page = urllib2.urlopen(doistr)
        if page.geturl()[-8:] == 'abstract':
            full = page.geturl()[:-8] + 'full'
        elif page.geturl()[-4:] == 'full':
            full = page.geturl()
        print(full)
        page = urllib2.urlopen(full)
        with open('temp', 'w') as temp:
            temp.write(page.read())
        images = []
        with open('temp', 'r') as temp:
            for l in temp.readlines():
                images += re.findall('<a href="(?P<href>http://\w{7}.\w{3}.\w{3}.rackcdn.com/\d{5}/f\w{4}-\d{2}-\d{5}-HTML/image_m/f\w{4}-\d{2}-\d{5}-\D{1,2}\d{3}.\D{3})', l)
                images += re.findall('<img src="(?P<src>http://\w{7}.\w{3}.\w{3}.rackcdn.com/\d{5}/f\w{4}-\d{2}-\d{5}-HTML/image_n/f\w{4}-\d{2}-\d{5}-\D{1,2}\d{3}.\D{3})', l)
        os.remove('temp')
    for i in images:
        loc = os.path.join(img_dir, i.split('-')[-1])
        downloadImage(i, loc)
        print('Downloaded image {0}'.format(loc))
    if images:
        checkEquationCompletion(images)
    print("Done downloading images")
    #If the images were not already cached, and caching is enabled...
    #We want to transfer the downloaded files to the cache
    if caching:
        os.mkdir(art_cache)
        shutil.copytree(img_dir, art_cache_images)
