import utils
import metadata
import logging
import xml.dom.minidom as minidom


class Article(object):
    '''
    A journal article; the top-level element (document element) of the
    Journal Publishing DTD, which contains all the metadata and content for
    the article.
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
        self.attrs = {'article-type': None, 'dtd-version': None,
                      'xml:lang': None, 'xmlns:mml': None,
                      'xmlns:xlink': None, 'xmlns:xsi': None}
        for attr in self.attrs:
            #getAttribute() returns an empty string if the attribute DNE
            self.attrs[attr] = self.root_tag.getAttribute(attr)
        self.validateAttrs()  # Log errors for invalid attribute values
        #The following, in order:
        #<front> Front Matter
        #<body> Body of the Article, zero or one
        #<back> Back Matter, zero or one
        #<floats-group> Floating Element Group, zero or one
        #Any one of:
        #    <sub-article> Sub-Article, zero or more
        #    <response> Response, zero or more
        #
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
        ###
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
        self.front = Front(front_node)
        if back_node:
            self.back = Back(back_node[0])
        else:
            self.back = None
        #We could do the same for Body, but it is not needed.
        if body_node:
            self.body = body_node[0]
        else:
            self.body = None

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
            if not self.attrs[_key] == _val:
                logging.error(attr_err.format(_key, self.attrs[_key]))

        if self.attrs['article-type'] not in utils.suggestedArticleTypes():
            art_type_err = 'article-type value is not a suggested value: {0}'
            logging.warning(art_type_err.format(self.attrs['article-type']))

    def getDOI(self):
        '''A method for returning the DOI identifier of an article'''
        for (_data, _id) in self.front.article_meta.identifiers:
            if _id == 'doi':
                return(_data)

    def titlestring(self):
        '''Creates a string which may be used as the title if desired.'''
        jmet = self.front.journal_meta
        amet = self.front.article_meta
        titlestring = u'{0}_{1}{2}'.format(jmet.identifier['pmc'],
                                           amet.art_auths[0].get_surname(),
                                           amet.art_dates['epub'].year)
        titlestring = titlestring.replace(u' ', u'-')
        return(titlestring)

    def fetchPLoSImages(self, cache_dir, output_dir, caching):
        '''Fetch the images associated with the article.'''
        import urllib2
        import logging
        import os.path
        import shutil
        from time import sleep
        
        print('Processing images...')
        doi = self.getDOI()
        o = doi.split('journal.')[1]
        img_dir = os.path.join(output_dir, 'OPS', 'images-{0}'.format(o))
        #Check cache to see if images already have been downloaded
        cached = False
        p, s = os.path.split(doi)
        if p == '10.1371':
            art_cache = os.path.join(cache_dir, 'PLoS', s)
            art_cache_images = os.path.join(art_cache, 'images')
            if os.path.isdir(art_cache):
                cached = True
                logging.info('Cached images found')
                print('Cached images found. Transferring from cache...')
                shutil.copytree(art_cache_images, img_dir)
            else:
                logging.info('Cached images not found')
        else:
            print('The publisher DOI does not correspond to PLoS')
        
        if not cached:
            model_images = os.path.join(cache_dir, 'model', 'images')
            shutil.copytree(model_images, img_dir)
            print('Downloading images, this may take some time...')
            #This string is invariable in the fetching of PLoS images
            PLOSSTRING = 'article/fetchObject.action?uri=info%3Adoi%2F'
            #An example DOI for PLoS is 10.1371/journal.pmed.0010027
            #Here we parse it into useful strings for URL construction
            pdoi, jdoi = doi.split('/')  # 10.1371, journal.pmed.0010027
            _j, jrn_id, art_id = jdoi.split('.')  # journal, pmed, 0010027
            #A mapping of journal ids to URLs:
            jids = {'pgen': 'http://www.plosgenetics.org/',
                    'pcbi': 'http://www.ploscompbiol.org/',
                    'ppat': 'http://www.plospathogens.org/',
                    'pntd': 'http://www.plosntds.org/',
                    'pmed': 'http://www.plosmedicine.org/',
                    'pbio': 'http://www.plosbiology.org/',
                    'pone': 'http://www.plosone.org/'}
            #A mapping of image types to directory names
            dirs = {'e': 'equations', 'g': 'figures', 't': 'tables'}
            #We detect all the graphic references in the document
            graphics = self.root_tag.getElementsByTagName('graphic')
            graphics += self.root_tag.getElementsByTagName('inline-graphic')
            for g in graphics:
                xlink_href = g.getAttribute('xlink:href')
                tag = xlink_href.split('.')[-1]
                type = tag[0]  # first character, either e, g, or t
                if type == 'e':  # the case of an equation
                    rep = '&representation=PNG'
                else:  # other cases: table and figure
                    rep = '&representation=PNG_L'
                #Let's compose the address
                addr_str = '{0}{1}{2}%2Fjournal.{3}.{4}.{5}{6}'
                addr = addr_str.format(jids[jrn_id], PLOSSTRING, pdoi, jrn_id,
                                       art_id, tag, rep)
                #Open the address
                try:
                    image = urllib2.urlopen(addr)
                except urllib2.HTTPError, e:
                    if e.code == 503:  # Server overloaded
                        sleep(1)  # Wait one second
                        try:
                            image = urllib2.urlopen(address)
                        except:
                            break
                    elif e.code == 500:
                        logging.error('urllib2.HTTPError {0}'.format(e.code))
                    break
                else:
                    filename = '{0}.png'.format(tag)
                    img_dir_sub = dirs[type]
                    img_file = os.path.join(img_dir, img_dir_sub, filename)
                    with open(img_file, 'wb') as outimage:
                        outimage.write(image.read())
                    dl_str = 'Downloaded image {0}'
                    print(dl_str.format(tag))
            print("Done downloading images")
        #If the images were not already cached, and caching is enabled...
        #We want to transfer the downloaded files to the cache
        if not cached and caching:
            os.mkdir(art_cache)
            shutil.copytree(img_dir, art_cache_images)

class Front(object):
    '''The metadata for an article, such as the name and issue of the journal
    in which the article appears and the author(s) of the article'''

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
    '''The back element for an article, contains footnotes, funding, competing
    and interests'''
    def __init__(self, node):
        self.node = node
        self.footnotes = node.getElementsByTagName('fn')
        self.funding = u''
        self.competing_interests = u''
        for item in self.footnotes:
            if item.getAttribute('fn-type') == u'conflict':
                text = utils.serializeText(item, stringlist=[])
                self.competing_interests = text
            elif item.getAttribute('fn-type') == u'financial-disclosure':
                text = utils.serializeText(item, stringlist=[])
                self.funding = text
                
        try:
            ack_node = node.getElementsByTagName('ack')[0]
        except IndexError:
            self.ack = None
        else:
            self.ack = ack_node
        try:
            gloss = node.getElementsByTagName('glossary')[0]
        except IndexError:
            self.glossary = None
        else:
            self.glossary = gloss