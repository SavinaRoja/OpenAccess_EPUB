import utils
import logging
import sys
import xml.dom.minidom
import jptsmeta


class Article(object):
    """
    A journal article; the top-level element (document element) of the
    Journal Publishing DTD, which contains all the metadata and content for
    the article.
    3.0 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/3.0/n-3q20.html
    2.0 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-9kc0.html
    2.3 Tagset:
    http://dtd.nlm.nih.gov/publishing/tag-library/2.3/n-zxc2.html
    """
    def __init__(self, xml_file):
        """
        The __init__() method has to do the following specific jobs. It must
        parse the article using xml.dom.minidom. It must check the parsed
        article to detect its DTD and version; it must also detect the
        publisher using self.identifyPublisher(). It is responsible for
        using this information to create an instance of a metadata class
        such as found in jptsmeta.py to serve as the article's metadata
        attribute.
        """
        logging.info('Parsing file: {0}'.format(xml_file))
        doc = xml.dom.minidom.parse(xml_file)
        #Here we check the doctype for the DTD under which the article was
        #published. This affects how we will parse metadata and content.
        dtds = {u'-//NLM//DTD Journal Publishing DTD v2.0 20040830//EN':
                u'2.0',
                u'-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN':
                u'2.3',
                u'-//NLM//DTD Journal Publishing DTD v3.0 20080202//EN':
                u'3.0'}
        try:
            self.dtd = dtds[doc.doctype.publicId]
            dtdStatus = 'Article published with Journal Publishing DTD v{0}'
            print(dtdStatus.format(self.dtd))
        except KeyError:
            print('The article\'s DOCTYPE declares an unsupported Journal \
Publishing DTD: \n{0}'.format(doc.doctype.publicId))
            sys.exit()
        #Access the root tag of the document
        self.root_tag = doc.documentElement
        #Determine the publisher
        self.publisher = self.identifyPublisher()
        print(self.publisher)
        #Create instance of article metadata
        if self.dtd == u'2.0':
            self.metadata = jptsmeta.JPTSMeta20(doc, self.publisher)
        elif self.dtd == u'2.3':
            self.metadata = jptsmeta.JPTSMeta23(doc, self.publisher)
        elif self.dtd == u'3.0':
            self.metadata = jptsmeta.JPTSMeta30(doc, self.publisher)
        #The <article> tag has a handful of potential attributes, we can check
        #to make sure the mandated ones are valid
        self.attrs = {'article-type': None, 'dtd-version': None,
                      'xml:lang': None, 'xmlns:mml': None,
                      'xmlns:xlink': None, 'xmlns:xsi': None}
        for attr in self.attrs:
            #getAttribute() returns an empty string if the attribute DNE
            self.attrs[attr] = self.root_tag.getAttribute(attr)
        self.validateAttrs()  # Log errors for invalid attribute values

    def identifyPublisher(self):
        """
        This method determines the publisher of the document based on an
        an internal declaration. For both JP-DTDv2.0 and JP-DTDv2.3, there are
        two important signifiers of publisher, <publisher> under <journal-meta>
        and <article-id pub-id-type="doi"> under <article-meta>.
        """
        pubs = {u'Frontiers Research Foundation': u'Frontiers',
                u'Public Library of Science': u'PLoS'}
        dois = {u'10.3389': u'Frontiers',
                u'10.1371': u'PLoS'}
        if self.dtd in ['2.0', '2.3']:
            #The publisher node will be the primary mode of identification
            publisher = self.root_tag.getElementsByTagName('publisher')
            pname = False
            if publisher:
                pname = publisher[0].getElementsByTagName('publisher-name')[0]
                pname = pname.firstChild.data
                try:
                    return pubs[pname]
                except KeyError:
                    print('Strange publisher name: {0}'.format(pname))
                    print('Falling back to article-id DOI')
                    pname = False
            if not pname:  # If pname is undeclared, check article-id
                art_IDs = self.root_tag.getElementsByTagName('article-id')
                for aid in art_IDs:
                    if aid.getAttribute('pub-id-type') == u'doi':
                        idstring = aid.firstChild.data
                        pub_doi = idstring.split('/')[0]
                try:
                    return dois[pub_doi]
                except KeyError:
                    print('Unable to identify publisher by DOI, aborting!')
                    sys.exit()

    def validateAttrs(self):
        """
        Most of the time, attributes are not required nor do they have fixed
        values. But in this case, there are some mandatory requirements.
        """
        #I would love to check xml:lang against RFC 4646:
        # http://www.ietf.org/rfc/rfc4646.txt
        #I don't know a good tool for it though, so it gets a pass for now.
        mandates = [('xmlns:mml', 'http://www.w3.org/1998/Math/MathML'),
                    ('xmlns:xlink', 'http://www.w3.org/1999/xlink'),
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

    def fetchPLoSImages(self, cache_dir, output_dir, caching):
        '''Fetch the PLoS images associated with the article.'''
        import urllib2

        import os.path
        import shutil
        from time import sleep

        doi = self.getDOI()
        print('Processing images for {0}...'.format(doi))
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
                typechar = tag[0]  # first character, either e, g, or t
                if typechar == 'e':  # the case of an equation
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
                            image = urllib2.urlopen(addr)
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

    def fetchFrontiersImages(self, cache_dir, output_dir, caching):
        '''Fetch the Frontiers images associated with the article.'''
        pass
