'''utility/common stuff'''
import os.path
from collections import namedtuple

Identifier = namedtuple('Identifer', 'id, type')

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

def recursive_zip(zipf, directory, folder = ""):
    '''Recursively traverses the output directory to construct the zipfile'''
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), os.path.join(directory,
                                                                   item))
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(zipf, os.path.join(directory, item),
                          os.path.join(folder, item))

def fetchPLoSImages(doidata, cache_dir, output_dir, caching):
    '''Fetch the images associated with the article.'''
    
    import urllib2, logging, os.path, shutil
    import output
    from time import sleep
     
    print('Processing images...')
    
    output_dir_images = os.path.join(output_dir, 'OPS', 'images')
    
    #Check cache to see if images already have been downloaded
    cached = False
    prefix, suffix = os.path.split(doidata)
    if prefix == '10.1371':
        publisher = 'PLoS'
        art_cache = os.path.join(cache_dir, publisher, suffix)
        art_cache_images = os.path.join(art_cache, 'images')
        if os.path.isdir(art_cache):
            cached = True
            logging.info('Cached images found')
            print('Cached images found. Transferring from cache...')
            shutil.copytree(art_cache_images, output_dir_images)
        else:
            logging.info('Cached images not found')
    
    if not cached:
        model_images = os.path.join(cache_dir, 'model', 'images')
        shutil.copytree(model_images, output_dir_images)
        print('Downloading images, this may take some time...')
        if publisher == 'PLoS':
            PLOSSTRING = 'article/fetchObject.action?uri=info%3Adoi%2F'
            #split the doidata into useful fragments
            slashsplit = doidata.split('/')
            journaldoi = slashsplit[0]
            dotsplit = slashsplit[1].split('.')
            journalid = dotsplit[1]
            articledoi = dotsplit[2]
            
            jids = {'pgen': 'http://www.plosgenetics.org/', 
                    'pcbi': 'http://www.ploscompbiol.org/', 
                    'ppat': 'http://www.plospathogens.org/', 
                    'pntd': 'http://www.plosntds.org/', 
                    'pmed': 'http://www.plosmedicine.org/', 
                    'pbio': 'http://www.plosbiology.org/',
                    'pone': 'http://www.plosone.org/'}
            
            imagetypes = [('g', 'figures', 'figure'), 
                          ('t', 'tables', 'table'), 
                          ('e', 'equations', 'equation')]
            
            for itype, subdirect, itype_str in imagetypes:
                    
                for refnum in range(1,10000):
                    addr_str = '{0}{1}{2}%2Fjournal.{3}.{4}.{5}{6}&representation=PNG_L'
                    address = addr_str.format(jids[journalid], PLOSSTRING, 
                                              journaldoi, journalid, 
                                              articledoi, itype,
                                              str(refnum).zfill(3))
                    if itype == 'e':
                        address = address[:-2]
                        
                    try:
                        image = urllib2.urlopen(address)
                        
                    except urllib2.HTTPError, e:
                        if e.code == 503: #Server overloaded
                            sleep(1) #wait a second
                            try:
                                image = urllib2.urlopen(address)
                            except:
                                break
                        elif e.code == 500:
                            logging.error('urllib2.HTTPError {0}'.format(e.code))
                        break
                        
                    else:
                        filename = '{0}{1}.png'.format(itype, str(refnum).zfill(3))
                        image_file = os.path.join(output_dir_images, 
                                                  subdirect, filename)
                        with open(image_file, 'wb') as outimage:
                            outimage.write(image.read())
                        dl_str = 'Downloaded {0} image {1}{2}'
                        print(dl_str.format(itype_str, itype, str(refnum).zfill(3)))
                        
                    refnum += 1
        print('Done downloading images')
    if caching and not cached:
        os.mkdir(art_cache)
        shutil.copytree(output_dir_images, art_cache_images)
        


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