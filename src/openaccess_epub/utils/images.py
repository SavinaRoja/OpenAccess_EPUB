# -*- coding: utf-8 -*-
"""
Utility suite for handling images.
"""

import urllib.request
import urllib.error
import time
import re
import os.path
import shutil
import logging
import openaccess_epub.utils as utils


log = logging.getLogger('utils.images')


def local_images(images_path, outdirect, doi):
    """
    This function is employed to copy image files into the ePub's image
    directory, it expects an existing directory.
    """
    jdoi, adoi = doi.split('/')
    log.debug('Journal DOI-{0}|Article DOI{1}'.format(jdoi, adoi))
    epub_img_dir = os.path.join(outdirect, 'OPS', 'images-{0}'.format(adoi))
    log.info('ePub image directory path: {0}'.format(epub_img_dir))
    os.mkdir(epub_img_dir)
    for item in os.listdir(images_path):
        item_path = os.path.join(images_path, item)
        if os.path.splitext(item_path)[1] == '.tif':
            shutil.copy2(item_path, epub_img_dir)


def move_images_to_cache(source, destination):
    """
    Handles the movement of images to the cache. Must be helpful if it finds
    that the folder for this article already exists.
    """
    print('Moving images to cache, {0}'.format(destination))
    try:
        shutil.copytree(source, destination)
    except OSError:  # Should occur if the folder already exists
        print('An image cache for this article already appears to exist!')
        print('Would you like to replace it?')
        choice = raw_input('[y/N]')
        if choice in ['y', 'Y']:
            shutil.rmtree(destination)
            log.debug('Previous cache removed: {0}'.format(destination))
            shutil.copytree(source, destination)


def explicit_images(images, config, img_dir):
    """
    The method used to handle an explicitly defined image directory by the
    user as a parsed argument.
    """
    log.info('Explicit image directory specified: {0}'.format(images))
    shutil.copytree(manual_images, img_dir)
    if config.use_image_cache:
        move_images_to_cache(manual_images, article_cache)
    return True


def input_relative_images(config, img_dir):
    """
    The method used to handle Input-Relative image inclusion.
    """
    for dir in config.input_relative_images:
        if os.path.isdir(dir):
            log.info('Input-Relative image directory found: {0}'.format(dir))
            shutil.copytree(dir, img_dir)
            if config.use_image_cache:
                move_images_to_cache(dir, article_cache)
            return True
    return False


def image_cache(article_cache, img_dir):
    """
    The method to be used by get_images() for copying images out of the cache.
    """
    if os.path.isdir(article_cache):
        log.info('Cached image directory found: {0}'.format(article_cache))
        shutil.copytree(article_cache, img_dir)
        return True
    return False


def get_images(doi, outdirect, images, config, document):
    """
    This controls the logic for placing the appropriate image files into the
    ePub directory.

    The function will attempt to incorporate the images according to priority
    as follows: Manually specified image directory (argument flag), default
    image location (a known place to look, such as ./images/), fetched from
    the cache (if the images have been downloaded and cached previously).

    If unable to find images through manual specification, default location, or
    the cache, get_images will call the appropriate function to download the
    images from the internet (publisher's website).

    Caching=True will ensure that the images are added to the cache.
    """
    #Split the DOI
    journal_doi, article_doi = doi.split('/')
    log.debug('journal-doi-{0}'.format(journal_doi))
    log.debug('article-doi-{0}'.format(article_doi))

    #Specify where to place the images in the output
    img_dir = os.path.join(outdirect, 'OPS', 'images-{0}'.format(article_doi))
    log.info('Constructed image directory as {0}'.format(img_dir))

    #Construct path to cache for article
    article_cache = os.path.join(config.image_cache, journal_doi, article_doi)

    #Use manual image directory, explicit images
    if images:
        #Explicit images prevents all other image methods
        return explicit_images(images, config, img_dir)

    #Input-Relative import, looks for any one of the listed options
    if config.use_input_relative_images:
        #Prevents other image methods only if successful
        if input_relative_images(config, img_dir):
            return True

    #Use cache for article if it exists
    if config.use_image_cache:
        #Prevents other image methods only if successful
        if image_cache(article_cache, img_dir):
            return True

    #Download images from Internet
    if config.use_image_fetching:
        os.mkdir(img_dir)
        if journal_doi == '10.3389':
            fetch_frontiers_images(article_doi, img_dir)
            if config.use_image_cache:
                move_images_to_cache(img_dir, article_cache)
            return True
        elif journal_doi == '10.1371':
            success = fetch_plos_images(article_doi, img_dir, document)
            if success:
                if config.use_image_cache:
                    move_images_to_cache(img_dir, article_cache)
            return success
        else:
            print('Fetching images for this publisher is not supported!')
            return False
    return False


def make_image_cache(img_cache):
    """
    Initiates the image cache if it does not exist
    """
    log.info('Initiating the image cache at {0}'.format(img_cache))
    if not os.path.isdir(img_cache):
        utils.mkdir_p(img_cache)
        utils.mkdir_p(os.path.join(img_cache, '10.1371'))
        utils.mkdir_p(os.path.join(img_cache, '10.3389'))


def fetch_frontiers_images(doi, output_dir):
    """
    Fetch the images from Frontiers' website. This method may fail to properly
    locate all the images and should be avoided if the files can be accessed
    locally. Downloading the images to an appropriate directory in the cache,
    or to a directory specified by passed argument are the preferred means to
    access images.
    """
    log.info('Fetching Frontiers images')
    log.warning('This method may fail to locate all images.')

    def download_image(fetch, img_file):
        try:
            image = urllib.request.urlopen(fetch)
        except urllib.error.HTTPError as e:
            if e.code == 503:  # Server overloaded
                time.sleep(1)  # Wait one second
                try:
                    image = urllib.request.urlopen(fetch)
                except:
                    return None
            elif e.code == 500:
                print('urllib.error.HTTPError {0}'.format(e.code))
            return None
        else:
            with open(img_file, 'wb') as outimage:
                outimage.write(image.read())
        return True

    def check_equation_completion(images):
        """
        In some cases, equations images are not exposed in the fulltext (hidden
        behind a rasterized table). This attempts to look for gaps and fix them
        """
        log.info('Checking for complete equations')
        files = os.listdir(output_dir)
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
            loc = os.path.join(output_dir, m)
            download_image(get + m, loc)
            print('Downloaded image {0}'.format(loc))
        #It is possible that we need to go further than the highest
        highest += 1
        name = 'i{0}.gif'.format(str(highest).zfill(3))
        loc = os.path.join(output_dir, name)
        while download_image(get + name, loc):
            print('Downloaded image {0}'.format(loc))
            highest += 1
            name = 'i{0}.gif'.format(str(highest).zfill(3))

    print('Processing images for {0}...'.format(doi))
    #We use the DOI of the article to locate the page.
    doistr = 'http://dx.doi.org/{0}'.format(doi)
    logging.debug('Accessing DOI address-{0}'.format(doistr))
    page = urllib.request.urlopen(doistr)
    if page.geturl()[-8:] == 'abstract':
        full = page.geturl()[:-8] + 'full'
    elif page.geturl()[-4:] == 'full':
        full = page.geturl()
    print(full)
    page = urllib.request.urlopen(full)
    with open('temp', 'w') as temp:
        temp.write(page.read())
    images = []
    with open('temp', 'r') as temp:
        for l in temp.readlines():
            images += re.findall('<a href="(?P<href>http://\w{7}.\w{3}.\w{3}.rackcdn.com/\d{5}/f\w{4}-\d{2}-\d{5}-HTML/image_m/f\w{4}-\d{2}-\d{5}-\D{1,2}\d{3}.\D{3})', l)
            images += re.findall('<a href="(?P<href>http://\w{7}.\w{3}.\w{3}.rackcdn.com/\d{5}/f\w{4}-\d{2}-\d{5}-r2/image_m/f\w{4}-\d{2}-\d{5}-\D{1,2}\d{3}.\D{3})', l)
            images += re.findall('<img src="(?P<src>http://\w{7}.\w{3}.\w{3}.rackcdn.com/\d{5}/f\w{4}-\d{2}-\d{5}-HTML/image_n/f\w{4}-\d{2}-\d{5}-\D{1,2}\d{3}.\D{3})', l)
    os.remove('temp')
    for i in images:
        loc = os.path.join(output_dir, i.split('-')[-1])
        download_image(i, loc)
        print('Downloaded image {0}'.format(loc))
    if images:
        check_equation_completion(images)
    print("Done downloading images")


def fetch_plos_images(article_doi, output_dir, document):
    """
    Fetch the images for a PLoS article from the internet.

    PLoS images are known through the inspection of <graphic> and
    <inline-graphic> elements. The information in these tags are then parsed
    into appropriate URLs for downloading.
    """
    print('Processing images for {0}...'.format(article_doi))

    #A dict of URLs for PLoS subjournals
    journal_urls = {'pgen': 'http://www.plosgenetics.org/article/{0}',
                    'pcbi': 'http://www.ploscompbiol.org/article/{0}',
                    'ppat': 'http://www.plospathogens.org/article/{0}',
                    'pntd': 'http://www.plosntds.org/article/{0}',
                    'pmed': 'http://www.plosmedicine.org/article/{0}',
                    'pbio': 'http://www.plosbiology.org/article/{0}',
                    'pone': 'http://www.plosone.org/article/{0}',
                    'pctr': 'http://clinicaltrials.ploshubs.org/article/{0]}'}

    #Identify subjournal name for base URl
    subjournal_name = article_doi.split('.')[1]
    base_url = journal_urls[subjournal_name]

    #Acquire <graphic> and <inline-graphic> xml elements
    graphics = document.root_tag.getElementsByTagName('graphic')
    graphics += document.root_tag.getElementsByTagName('inline-graphic')

    #Begin to download
    print('Downloading images, this may take some time...')
    for graphic in graphics:
        xlink_href = graphic.getAttribute('xlink:href')
        if xlink_href[-4] == 'e':  # Equations are handled differently
            resource = 'fetchObject.action?uri=' + xlink_href + '&representation=PNG'
        else:
            resource = xlink_href + '/largerimage'
        full_url = base_url.format(resource)
        try:
            image = urllib.request.urlopen(full_url)
        except urllib.error.HTTPError as e:
            if e.code == 503:  # Server overload error
                time.sleep(1)  # Wait a second
                try:
                    image = urllib.request.urlopen(full_url)
                except:
                    return False  # Happened twice, give up
            else:
                log.error('urllib.error.HTTPError {0}'.format(e.code))
            return False
        else:
            img_name = xlink_href.split('.')[-1] + '.png'
            img_path = os.path.join(output_dir, img_name)
            with open(img_path, 'wb') as output:
                output.write(image.read())
            print('Downloaded image {0}\n'.format(img_name))
    print('Done downloading images')
    return True
