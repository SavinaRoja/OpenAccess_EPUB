import front, body, back
import xml.dom.minidom as minidom

class Article(object):
    '''
    A journal article; the top-level element (document element) of the 
    Journal Publishing DTD, which contains all the metadata and content for 
    the article
    
    http://dtd.nlm.nih.gov/publishing/tag-library/2.0/index.html
    '''
    
    def __init__(self, document):
        
        self.inputstring = document
        doc = minidom.parse(self.inputstring)
        
        self.root_tag = doc.documentElement
        
        attr_strings = [u'article-type', u'dtd-version', u'xml:lang', u'xmlns:mml', u'xmlns:xlink']
        
        self.attributes = {}
        self.playorder = 1
        
        for attr in attr_strings:
            value = self.root_tag.getAttribute(attr)
            self.attributes[attr] = value
        
        
        if self.attributes[u'xmlns:mml'] != u'http://www.w3.org/1998/Math/MathML':
            print('ERROR: The MathML attribute value may not be changed from \'http://www.w3.org/1998/Math/MathML\'')
        
        if self.attributes[u'xmlns:xlink'] != u'http://www.w3.org/1999/xlink':
            print('ERROR: The XLink Namespace Declaration attribute value may not be changed from \'http://www.w3.org/1999/xlink\'')
        
        #Mandatory
        frontnode = self.root_tag.getElementsByTagName('front')[0]
        
        #Technically optional, but assume for now that they will be present
        self.bodynode = self.root_tag.getElementsByTagName('body')[0]
        self.backnode = self.root_tag.getElementsByTagName('back')[0]
        
        #It can have a <sub-article> or a <response>, but let's ignore that for now
        #try:
        #    subarticlenode = self.root_tag.getElementsByTagName('sub-article')[0]
        #except:
        #    try:
        #        responsenode = self.root_tag.getElementsByTagName('response')[0]
        #    except:
        #        pass
        
        self.front = front.Front(frontnode)
        self.body = body.Body(self.bodynode)
        self.back = back.Back(self.backnode)
        
        #Create an attribute element to hold the document's features
        self.features = doc.createElement('features')
        #Run the featureParse method to get feature tree
        self.featureParse(doc, self.bodynode, self.features)
        
        #print(self.features.toprettyxml(encoding = 'utf-8'))
        
    def titlestring(self):
        '''Creates a titlestring for use as the epub filename'''
        
        titlestring = u'{0}_{1}{2}'.format(self.front.journal_meta.identifier['pmc'],
                                           self.front.article_meta.art_auths[0].surname,
                                           self.front.article_meta.art_dates['collection'].year)
        titlestring = titlestring.replace(u' ', u'-')
        
        return titlestring
        
    def fetchImages(self, publisher = 'PLoS', dirname = 'test_output'): #Default to PLoS for now
        '''Fetch the images associated with the article.'''
        
        import urllib2, logging, os.path
        import output
        
        print('Downloading images. This may take some time...')
        
        for (_data, _id) in self.front.article_meta.identifiers:
            if _id == 'doi':
                doidata = _data
        
        if publisher == 'PLoS':
            
            PLOSSTRING = 'article/fetchObject.action?uri=info%3Adoi%2F'
            
            #split the doidata into useful fragments
            slashsplit = doidata.split('/')
            journaldoi = slashsplit[0]
            dotsplit = slashsplit[1].split('.')
            journalid = dotsplit[1]
            articledoi = dotsplit[2]
            
            if journalid == 'pgen':
                journalurl = 'http://www.plosgenetics.org/'
            elif journalid == 'pcbi':
                journalurl = 'http://www.ploscompbiol.org/'
            elif journalid == 'ppat':
                journalurl = 'http://www.plospathogens.org/'
            elif journalid == 'pntd':
                journalurl = 'http://www.plosntds.org/'
            elif journalid == 'pmed':
                journalurl = 'http://www.plosmedicine.org/'
            elif journalid == 'pbio':
                journalurl = 'http://www.plosbiology.org/'
            elif journalid == 'pone':
                journalurl = 'http://www.plosone.org/'
            
            imagetypes = [('g', 'figures', 'figure'), 
                          ('t', 'tables', 'table'), 
                          ('e', 'equations', 'equation')]
            
            for itype, subdirect, itype_str in imagetypes:
                    
                for refnum in range(1,1000):
                    addr_str = '{0}{1}{2}%2Fjournal.{3}.{4}.{5}{6}&representation=PNG_L'
                    address = addr_str.format(journalurl, PLOSSTRING, journaldoi,
                                              journalid, articledoi, itype,
                                              str(refnum).zfill(3))
                    
                    if itype == 'e':
                        address = address[:-2]
                        
                    try:
                        image = urllib2.urlopen(address)
                        
                    except urllib2.HTTPError, e:
                        if not e.code == 500:
                            logging.error('urllib2.HTTPError {0}'.format(e.code))
                        break
                        
                    else:
                        filename = '{0}{1}.png'.format(itype, str(refnum).zfill(3))
                        image_file = os.path.join(dirname, 'OPS', 'images',
                                                  subdirect, filename)
                        with open(image_file, 'wb') as outimage:
                            outimage.write(image.read())
                        print('Downloaded {0} image {1}{2}'.format(itype_str, 
                                                                   itype, 
                                                                   str(refnum).zfill(3)))
                        
                    refnum += 1
        print('Done downloading images')
        
    def featureParse(self, doc, fromnode, destnode):
        '''A method that traverses the node, extracting a hierarchy of specific
        tagNames'''
        import utils
        
        tagnamestrs = [u'sec', u'fig', u'table-wrap']
        
        for child in fromnode.childNodes:
            try:
                tagname = child.tagName
            except AttributeError:
                pass
            else:
                if tagname in tagnamestrs:
                    clone = child.cloneNode(deep = False)
                    try:
                        title_node = child.getElementsByTagName('title')[0]
                    except IndexError: #in the case that it has no title
                        title_node = doc.createElement('title')
                        title_node.appendChild(doc.createTextNode(''))
                        clone.appendChild(title_node.cloneNode(deep = True))
                        clone.setAttribute('playOrder', str(self.playorder))
                        clone.setAttribute('title', '')
                        self.playorder += 1
                        destnode.appendChild(clone)
                        self.featureParse(doc, child, clone)
                    except AttributeError: #TextNodes have no attribute tagName
                        pass
                    else:
                        clone.appendChild(title_node.cloneNode(deep = True))
                        clone.setAttribute('playOrder', str(self.playorder))
                        clone.setAttribute('title', 
                                           utils.serializeText(title_node, stringlist = []))
                        self.playorder += 1
                        destnode.appendChild(clone)
                        self.featureParse(doc, child, clone)