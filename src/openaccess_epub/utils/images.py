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


log = logging.getLogger('openaccess_epub.utils.images')


def move_images_to_cache(source, destination):
    """
    Handles the movement of images to the cache. Must be helpful if it finds
    that the folder for this article already exists.
    """
    if os.path.isdir(destination):
        log.debug('Cached images for this article already exist')
        return
    else:
        log.debug('Cache location: {0}'.format(destination))
        try:
            shutil.copytree(source, destination)
        except:
            log.exception('Images could not be moved to cache')
        else:
            log.info('Moved images to cache'.format(destination))


def explicit_images(images, image_destination, rootname, config):
    """
    The method used to handle an explicitly defined image directory by the
    user as a parsed argument.
    """
    log.info('Explicit image directory specified: {0}'.format(images))
    if '*' in images:
        images = images.replace('*', rootname)
        log.debug('Wildcard expansion for image directory: {0}'.format(images))
    try:
        shutil.copytree(images, image_destination)
    except:
        #The following is basically a recipe for log.exception() but with a
        #CRITICAL level if the execution should be killed immediately
        #log.critical('Unable to copy from indicated directory', exc_info=True)
        log.exception('Unable to copy from indicated directory')
        return False
    else:
        return True


def input_relative_images(input_path, image_destination, rootname, config):
    """
    The method used to handle Input-Relative image inclusion.
    """
    log.debug('Looking for input relative images')
    input_dirname = os.path.dirname(input_path)
    for path in config.input_relative_images:
        if '*' in path:
            path = path.replace('*', rootname)
            log.debug('Wildcard expansion for image directory: {0}'.format(path))
        images = os.path.normpath(os.path.join(input_dirname, path))
        if os.path.isdir(images):
            log.info('Input-Relative image directory found: {0}'.format(images))
            shutil.copytree(images, image_destination)
            return True
    return False


def image_cache(article_cache, img_dir):
    """
    The method to be used by get_images() for copying images out of the cache.
    """
    log.debug('Looking for image directory in the cache')
    if os.path.isdir(article_cache):
        log.info('Cached image directory found: {0}'.format(article_cache))
        shutil.copytree(article_cache, img_dir)
        return True
    return False


def get_images(output_directory, explicit, input_path, config, parsed_article):
    """
    Main logic controller for the placement of images into the output directory

    Controlling logic for placement of the appropriate imager files into the
    EPUB directory. This function interacts with interface arguments as well as
    the local installation config.py file. These may change behavior of this
    function in terms of how it looks for images relative to the input, where it
    finds explicit images, whether it will attempt to download images, and
    whether successfully downloaded images will be stored in the cache.

    Parameters
    ----------
    output_directory : str
        The directory path where the EPUB is being constructed/output
    explicit : str
        A directory path to a user specified directory of images. Allows *
        wildcard expansion.
    input_path : str
        The absolute path to the input XML file.
    config : config module
        The imported configuration module
    parsed_article : openaccess_epub.article.Article object
        The Article instance for the article being converted to EPUB
    """
    #Split the DOI
    journal_doi, article_doi = parsed_article.doi.split('/')
    log.debug('journal-doi : {0}'.format(journal_doi))
    log.debug('article-doi : {0}'.format(article_doi))

    #Get the rootname for wildcard expansion
    rootname = utils.file_root_name(input_path)

    #Specify where to place the images in the output
    img_dir = os.path.join(output_directory,
                           'EPUB',
                           'images-{0}'.format(article_doi))
    log.info('Using {0} as image directory target'.format(img_dir))

    #Construct path to cache for article
    article_cache = os.path.join(config.image_cache, journal_doi, article_doi)

    #Use manual image directory, explicit images
    if explicit:
        success = explicit_images(explicit, img_dir, rootname, config)
        if success and config.use_image_cache:
            move_images_to_cache(img_dir, article_cache)
        #Explicit images prevents all other image methods
        return success

    #Input-Relative import, looks for any one of the listed options
    if config.use_input_relative_images:
        #Prevents other image methods only if successful
        if input_relative_images(input_path, img_dir, rootname, config):
            if config.use_image_cache:
                move_images_to_cache(img_dir, article_cache)
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
            success = fetch_plos_images(article_doi, img_dir, parsed_article)
            if success and config.use_image_cache:
                move_images_to_cache(img_dir, article_cache)
            return success
        else:
            log.error('Fetching images for this publisher is not supported!')
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
    log.info('Processing images for {0}...'.format(article_doi))

    #A dict of URLs for PLoS subjournals
    journal_urls = {'pgen': 'http://www.plosgenetics.org/article/{0}',
                    'pcbi': 'http://www.ploscompbiol.org/article/{0}',
                    'ppat': 'http://www.plospathogens.org/article/{0}',
                    'pntd': 'http://www.plosntds.org/article/{0}',
                    'pmed': 'http://www.plosmedicine.org/article/{0}',
                    'pbio': 'http://www.plosbiology.org/article/{0}',
                    'pone': 'http://www.plosone.org/article/{0}',
                    'pctr': 'http://clinicaltrials.ploshubs.org/article/{0}'}

    #Identify subjournal name for base URL
    subjournal_name = article_doi.split('.')[1]
    base_url = journal_urls[subjournal_name]

    #Acquire <graphic> and <inline-graphic> xml elements
    graphics = document.document.getroot().findall('.//graphic')
    graphics += document.document.getroot().findall('.//inline-graphic')

    #Begin to download
    log.info('Downloading images, this may take some time...')
    for graphic in graphics:
        nsmap = document.document.getroot().nsmap
        xlink_href = graphic.attrib['{' + nsmap['xlink'] + '}' + 'href']

        #Equations are handled a bit differently than the others
        #Here we decide that an image name starting with "e" is an equation
        if xlink_href.split('.')[-1].startswith('e'):
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
            log.info('Downloaded image {0}'.format(img_name))
    log.info('Done downloading images')
    return True
