"""
Utility suite for handling images.
"""

import urllib2
import time
import re
import os.path
import shutil
import logging


log = logging.getLogger('utils.images')


def getImages(doi, argimages, outdirect, default, caching, cache_img):
    """
    This controls the logic for placing the appropriate image files into the
    ePub directory.
    """
    #Order of operations: passed image directory, default image directory,
    #image cache, fetch from internet.
    #When complete: If caching is true, copy images to cache.
    jdoi, adoi = doi.split('/')  # Split DOI into journal, article components
    log.debug('jdoi-{0}| adoi-{1}'.format(jdoi, adoi))
    img_dir = os.path.join(outdirect, 'OPS', 'images-{0}'.format(adoi))
    log.info('Constructed image directory as {0}'.format(img_dir))
    if argimages:  # If manual input provided, use it
        shutil.copytree(argimages, img_dir)
        log.info('Copied images from {0}'.format())
    else:  # Fall back to the default, cache, or download
        #Check the default image directory
        if os.path.isdir(default):
            shutil.copytree(default, img_dir)
        else:
            #Check the image cache
            c = {'10.3389': 'Frontiers', '10.1371': 'PloS'}[jdoi]
            ac = os.path.join(cache_img, c, adoi)
            if os.path.isdir(ac):
                shutil.copytree(ac, img_dir)
                log.info('Copied images from cache-{0}'.format(ac))
            else:
                #Download from the internet
                if jdoi == '10.3389':
                    fetchFrontiersImages(doi, img_dir)
                elif jdoi == '10.1371':
                    fetchPLoSImages(doi, img_dir)
    if caching:
        if os.path.isdir(ac):  # Remove previous cache and replace with new
            #WARNING: shutil.rmtree() is a recursive deletion function, take
            #care when modifying this code
            shutil.rmtree(ac)
        shutil.copytree(img_dir, ac)


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


def fetchFrontiersImages(doi, output_dir):
    """
    Fetch the images from Frontiers' website. This method may fail to properly
    locate all the images and should be avoided if the files can be accessed
    locally. Downloading the images to an appropriate directory in the cache,
    or to a directory specified by passed argument are the preferred means to
    access images.
    """
    log.info('Fetching Frontiers images')
    log.warning('This method may fail to locate all images.')

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
    adoi = doi.split('/')[1]
    img_dir = os.path.join(output_dir, 'OPS', 'images-{0}'.format(adoi))
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


def fetchPLoSImages(doi, cache_dir, output_dir, caching):
    """
    Fetch the images from PLoS's website.
    """
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
            log.info('Cached images found')
            print('Cached images found. Transferring from cache...')
            shutil.copytree(art_cache_images, img_dir)
        else:
            log.info('Cached images not found')
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
                    log.error('urllib2.HTTPError {0}'.format(e.code))
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
