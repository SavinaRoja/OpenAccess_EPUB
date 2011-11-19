import utils
import metadata
import logging
import front, body
import xml.dom.minidom as minidom

class Article(object):
    '''
    A journal article; the top-level element (document element) of the 
    Journal Publishing DTD, which contains all the metadata and content for 
    the article
    
    3.0 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/3.0/n-3q20.html
    
    2.0 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-9kc0.html
    '''
    
    def __init__(self, xml_file):
        
        logging.info('Parsing file: {0}'.format(xml_file))
        doc = minidom.parse(xml_file)
        self.root_tag = doc.documentElement
        
        #The potential Attributes of the <article> tag
        #article-type Type of Article
        #dtd-version Version of the Tag Set (DTD)
        #xml:lang Language
        #xmlns:mml MathML Namespace Declaration
        #xmlns:xlink XLink Namespace Declaration
        #xmlns:xsi XML Schema Namespace Declaration
        
        self.attrs = {'article-type': None, 'dtd-version': None, 'xml:lang': None, 
                      'xmlns:mml': None, 'xmlns:xlink': None, 'xmlns:xsi': None}
        
        for attr in self.attrs:
            #getAttribute() returns an empty string if the attribute DNE
            self.attrs[attr] = self.root_tag.getAttribute(attr)
            
        self.validateAttrs() #Log errors for invalid attribute values
        
        #The following, in order:
        #<front> Front Matter
        #<body> Body of the Article, zero or one
        #<back> Back Matter, zero or one
        #<floats-group> Floating Element Group, zero or one
        #Any one of:
        #    <sub-article> Sub-Article, zero or more
        #    <response> Response, zero or more
        
        #When getElementsByTagName() does not find any elements, it creates an 
        #empty NodeList. It will thus evaluate False in control flow, consider 
        #the following approaches: I have come to prefer the latter...
        #
        #try:
        #    zero_or_one = self.root_tag.getElementsByTagName('zero-or-one')[0]
        #except IndexError:
        #    zero_or_one = None
        #    logging.info('zero-or-one tag not found')
        #----------------------------------------------------------------------
        #zero_or_one = self.root_tag.getElementsByTagName('zero-or-one')
        #if zero_or_one:
        #    doStuffWith(zero_or_one[0])
        
        #This tag is mandatory, bad input here deserves an error
        try:
            front_node = self.root_tag.getElementsByTagName('front')[0]
        except IndexError:
            msg = '<front> element was not detected in the document'
            logging.critical(msg)
            print(msg)
            sys.exit()
        #These tags are not mandatory, but rather expected...
        body_node = self.root_tag.getElementsByTagName('body')
        back_node = self.root_tag.getElementsByTagName('back')
        
        #This tag is new to 3.0, I don't know what to expect of it yet
        floats_group_node = self.root_tag.getElementsByTagName('floats-group')
        
        #These tags are zero or more, and mutually exclusive
        sub_article_nodes = self.root_tag.getElementsByTagName('sub-article')
        if not sub_article_nodes:
            response_nodes = self.root_tag.getElementsByTagName('response')
        
        #To make our lives easier (I hope), we can instantiate special classes 
        #for Front and Back nodes.
        self.front = Front(front_node[0])
        if back_node:
            self.back = Back(back_node[0])
        else:
            self.back = None
        #We could do the same for Body, but it is not needed.
        if body_node:
            self.body = body_node[0]
        else:
            self.body = None
        
        
        self.playorder = 2
        
        #Create an attribute element to hold the document's features
        self.features = doc.createElement('features')
        #Run the featureParse method to get feature tree
        self.featureParse(doc, self.bodynode, self.features)
        
    def validateAttrs(self):
        '''Most of the time, attributes are not required nor do they have fixed
         values. But in this case, there are some mandatory requirements.'''
        #I would love to check xml:lang against RFC 4646: 
        # http://www.ietf.org/rfc/rfc4646.txt
        #I don't know a good tool for it though, so it gets a pass for now.
        
        mandates = [('xmlns:mml', 'http://www.w3.org/1998/Math/MathML'), 
                    ('xmlns:xlink', 'http://www.w3.org/1999/xlink'), 
                    ('dtd-version', '3.0'), 
                    ('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')]
        
        attr_err = 'Article attribute {0} has improper value: {1}'
        
        for _key, _val in mandates:
            if not self.attrs(_key) == _val:
                logging.error(attr_err.format(_key, self.attrs(_key)))
        
        if self.attrs['article-type'] not in utils.suggestedArticleTypes():
            art_type_err = 'article-type value is not a suggested value: {0}'
            logging.warning(art_type_err.format(self.attrs['article-type']))
        
    def titlestring(self):
        '''Creates a titlestring for use as the epub filename'''
        
        titlestring = u'{0}_{1}{2}'.format(self.front.journal_meta.identifier['pmc'],
                                           self.front.article_meta.art_auths[0].get_surname(),
                                           self.front.article_meta.art_dates['epub'].year)
        titlestring = titlestring.replace(u' ', u'-')
        
        return titlestring
        
    def fetchImages(self, cache, publisher = 'PLoS', dirname = 'test_output'): #Default to PLoS for now
        '''Fetch the images associated with the article.'''
        
        import urllib2, logging, os.path, shutil
        import output
        from time import sleep
         
        print('Processing images...')
        
        for (_data, _id) in self.front.article_meta.identifiers:
            if _id == 'doi':
                doidata = _data
        
        #Check cache to see if images already have been downloaded
        cached = False
        prefix, suffix = os.path.split(doidata)
        if prefix == '10.1371':
            publisher = 'PLoS'
            cache_dir = os.path.join(cache, publisher, suffix)
            cache_dir_images = os.path.join(cache_dir, 'images')
            if os.path.isdir(cache_dir):
                cached = True
                logging.info('Cached images found')
                print('Cached images found. Transferring from cache...')
            else:
                logging.info('Cached images not found, creating cache...')
                os.mkdir(cache_dir)
                model_images = os.path.join(cache, 'model', 'images')
                shutil.copytree(model_images, cache_dir_images)
        
        if not cached:
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
                            image_file = os.path.join(cache_dir, 'images',
                                                      subdirect, filename)
                            with open(image_file, 'wb') as outimage:
                                outimage.write(image.read())
                            print('Downloaded {0} image {1}{2}'.format(itype_str, 
                                                                       itype, 
                                                                       str(refnum).zfill(3)))
                            
                        refnum += 1
            print('Done downloading images')
        
        dirname_ops_images = os.path.join(dirname, 'OPS', 'images')
        shutil.copytree(cache_dir_images, dirname_ops_images)
        
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

class Front(object):
    
    '''
    The metadata for an article, such as the name and issue of the journal 
    in which the article appears and the author(s) of the article
    '''
    
    def __init__(self, node):
        #Front may have no attributes
        self.root_tag = node
        
        #It must have a <journal-meta>
        journalmetanode = self.root_tag.getElementsByTagName('journal-meta')[0]
        self.journal_meta = metadata.JournalMeta(journalmetanode)
        
        #It must have a <article-meta>
        articlemetanode = self.root_tag.getElementsByTagName('article-meta')[0]
        self.article_meta = metadata.ArticleMeta(articlemetanode)
        

class Back(object):
    
    def __init__(self, node):
        self.footnotes = node.getElementsByTagName('fn')
        self.funding = u''
        self.competing_interests = u''
        for item in self.footnotes:
            if item.getAttribute('fn-type') == u'conflict':
                text = utils.serializeText(item, stringlist = [])
                self.competing_interests = text
            elif item.getAttribute('fn-type') == u'financial-disclosure':
                text = utils.serializeText(item, stringlist = [])
                self.funding = text