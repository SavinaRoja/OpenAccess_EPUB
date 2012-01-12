'''utility/common stuff'''
import os.path
import zipfile
from collections import namedtuple

Identifier = namedtuple('Identifer', 'id, type')

def makeEPUBBase(location, css_location):
    '''Contains the  functionality to create the ePub directory hierarchy from 
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
    base_epub/OPS/images/tables/'''
    
    #Create root directory
    rootname = location
    os.mkdir(rootname)
    #Create mimetype file in root directory
    mime_path = os.path.join(rootname, 'mimetype')
    with open(mime_path, 'w') as mimetype:
        mimetype.write('application/epub+zip')
    #Create OPS and META-INF directorys
    os.mkdir(os.path.join(rootname, 'META-INF'))
    os.mkdir(os.path.join(rootname, 'OPS'))
    #Create container.xml file in META-INF
    meta_path = os.path.join(rootname, 'META-INF', 'container.xml')
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
    os.mkdir(os.path.join(rootname, 'OPS', 'css'))
    css_path = os.path.join(rootname, 'OPS', 'css', 'article.css')
    with open(css_path, 'w') as css_out:
        with open(css_location, 'r') as css_src:
            css_out.write(css_src.read())

def createDCElement(document, name, data, attributes = None):
    '''A convenience method for creating DC tag elements.
    Used in content.opf'''
    newnode = document.createElement(name)
    newnode.appendChild(document.createTextNode(data))
    if attributes:
        for attr, attrval in attributes.iteritems():
            newnode.setAttribute(attr, attrval)
    
    return newnode

def stripDOMLayer(oldnodelist, depth = 1):
    '''This method strips layers \"off the top\" from a specified NodeList or 
    Node in the DOM. All child Nodes below the stripped layers are returned as
    a NodeList, treating them as siblings irrespective of the original 
    hierarchy. To be used with caution. '''
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

def serializeText(fromnode, stringlist = [], sep = u''):
    '''Recursively extract the text data from a node and it's children'''
    for item in fromnode.childNodes:
        if item.nodeType == item.TEXT_NODE and not item.data == u'\n':
            stringlist.append(item.data)
        else:
            serializeText(item, stringlist, sep)
    return sep.join(stringlist)
    
def getTagText(node):
    '''Grab the text data from a Node. If it is provided a NodeList, it will 
    return the text data from the first contained Node.'''
    data = u''
    try:
        children = node.childNodes
    except AttributeError:
        getTagText(node[0])
    else:
        if children:
            for child in children:
                if child.nodeType == child.TEXT_NODE and not child.data == u'\n':
                    data = child.data
            return data

def getFormattedNode(node):
    '''This method is called on a Node whose children may include emphasis 
    elements. The contained emphasis elements will be converted to ePub-safe
    emphasis elements. Non-emphasis elements will be untouched.'''
    
    #Some of these elements are to be supported through CSS
    emphasis_elements = [u'bold', u'italic', u'monospace', u'overline', 
                         u'sc', u'strike', u'underline']
    spans = {u'monospace': u'font-family:monospace', 
             u'overline': u'text-decoration:overline', 
             u'sc': u'font-variant:small-caps', 
             u'strike': u'text-decoration:line-through', 
             u'underline': u'text-decoration:underline'}
    
    clone = node.cloneNode(deep = True)
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
    '''Zips up the input file directory into an ePub file.'''
    epub_filename = outdirect + '.epub'
    epub = zipfile.ZipFile(epub_filename, 'w')
    current_dir = os.getcwd()
    os.chdir(outdirect)
    epub.write('mimetype')
    recursive_zip(epub, 'META-INF')
    recursive_zip(epub, 'OPS')
    os.chdir(current_dir)
    epub.close()

def recursive_zip(zipf, directory, folder = ""):
    '''Recursively traverses the output directory to construct the zipfile'''
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), os.path.join(directory,
                                                                   item))
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(zipf, os.path.join(directory, item),
                          os.path.join(folder, item))

def suggestedArticleTypes():
    '''Returns a list of suggested values for article-type'''
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
                     _publicId = '-//W3C//DTD XHTML 1.1//EN',
                     _systemId = 'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'):
    '''A method for conveniently initiating a new xml.DOM Document'''
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
    '''Uses Beautiful Soup to scrape the PLoS page of an issue. It is used
    instead of xml.dom.minidom because of malformed html/xml'''
    from BeautifulSoup import BeautifulStoneSoup
    import urllib2
    import os
    import os.path
    
    iu = urllib2.urlopen(issue_url)
    with open('temp','w') as temp:
        temp.write(iu.read())
    with open('temp', 'r') as temp:
        soup = BeautifulStoneSoup(temp)
    os.remove('temp')
    #Map the journal urls to nice strings
    jrns = {'plosgenetics': 'PLoS_Genetics', 'plosone' :'PLoS_ONE',
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
        