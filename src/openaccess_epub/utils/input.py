# -*- coding: utf-8 -*-
"""
This collection of utility functions are all related to passing input documents
to the OpenAccess_EPUB main function. They are all required to return the same
two things: the path to a local XML file, and an instance of Article made by
passing that file to the class.
"""

from OpenAccess_EPUB.article import Article
import urllib2
import urlparse
import sys
import os.path
import zipfile
import shutil
import logging

log = logging.getLogger('utils.input')


def get_file_root(full_path):
    """
    This method provides the standard mode of deriving the file root name from
    a given path to the file; excludes the file extension and all parent
    directories.
    """
    filename = os.path.split(full_path)[1]
    return os.path.splitext(filename)[0]


def local_input(xml_path):
    """
    This method accepts xml path data as an argument, instantiates the Article,
    and returns the two.
    """
    log.info('Local Input - {0}'.format(xml_path))
    art = Article(xml_path)
    return art, get_file_root(xml_path)


def doi_input(doi_string):
    """
    This method accepts a DOI string and attempts to download the appropriate
    xml file. If successful, it returns a path to that file along with an
    Article instance of that file. This works by requesting the correct page
    from http://dx.doi.org/ and then using publisher conventions to identify
    the article xml on that page.
    """
    log.info('DOI Input - {0}'.format(doi_string))
    pub_doi = {'10.1371': 'PLoS', '10.3389': 'Frontiers'}
    #A user might accidentally copy/paste the "doi:" part of a DOI
    if doi_string[:4]:
        doi_string = doi_string[4:]
    #Compose the URL to access at http://dx.doi.org
    doi_url = 'http://dx.doi.org/{0}'.format(doi_string)
    log.debug('DOI URL: {0}'.format(doi_url))
    #Report a problem specifying that the page could not be reached
    try:
        page = urllib2.urlopen(doi_url)
    except urllib2.URLError:
        err = '{0} could not be found. Check if the input was incorrect'
        print(err.format(doi_url))
        sys.exit(1)
    #How we proceed from here depends on the particular publisher
    try:
        publisher = pub_doi[doi_string.split('/')[0]]
    except KeyError:
        print('This publisher is not yet supported by OpenAccess_EPUB')
        sys.exit(1)
    if publisher == 'PLoS':
        address = urlparse.urlparse(page.geturl())
        log.debug('Rendered address: {0}'.format(address))
        path = address.path.replace(':', '%3A').replace('/', '%2F')
        fetch = '/article/fetchObjectAttachment.action?uri='
        aid = path.split('article%2F')[1]
        rep = '&representation=XML'
        access = '{0}://{1}{2}{3}{4}'.format(address.scheme, address.netloc,
                                    fetch, aid, rep)
        open_xml = urllib2.urlopen(access)
        filename = open_xml.headers['Content-Disposition'].split('\"')[1]
        with open(filename, 'wb') as xml_file:
            xml_file.write(open_xml.read())
        art = Article(filename)
        return art, get_file_root(filename)
    else:
        print('{0} is not supported for DOI Input'.format(publisher))
        sys.exit(1)


def url_input(url_string):
    """
    This method accepts a URL as an input and attempts to download the
    appropriate xml file from that page. This method is highly dependent on
    publisher conventions and may not be appropriate for all pusblishers.
    """
    log.info('URL Input - {0}'.format(url_string))
    support = ['PLoS']
    if '%2F10.1371%2F' in url_string:  # This is a PLoS page
        try:
            address = urlparse.urlparse(url_string)
            _fetch = '/article/fetchObjectAttachment.action?uri='
            _id = address.path.split('/')[2]
            _rep = '&representation=XML'
            access = '{0}://{1}{2}{3}{4}'.format(address.scheme,
                                                 address.netloc,
                                                 _fetch, _id, _rep)
            print('Opening {0}'.format(access.__str__()))
            open_xml = urllib2.urlopen(access)
        except:
            print('Unable to get XML from this address.')
            sys.exit(1)
        else:
            filename = open_xml.headers['Content-disposition'].split('\"')[1]
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
            art = Article(filename)
            #log.debug('Received XML path - {0}'.format(xml_path))
            return art, get_file_root(filename)
    else:  # We don't support this input or publisher
        print('Invalid Link: Bad URL or unsupported publisher')
        print('Supported publishers are: {0}'.format(', '.join(support)))
        sys.exit(1)


def frontiersZipInput(zip_path, output_prefix):
    """
    This method provides support for Frontiers production using base zipfiles
    as the input for ePub creation. It expects a valid pathname for one of the
    two zipfiles, and that both zipfiles are present in the same directory.
    """
    log.debug('frontiersZipInput called')
    #If there is a problem with the input, it should clearly describe the issue
    pathname, pathext = os.path.splitext(zip_path)
    path, name = os.path.split(pathname)
    if not pathext == '.zip':  # Checks for a path to zipfile
        log.error('Pathname provided does not end with .zip')
        print('Invalid file path: Does not have a zip extension.')
        sys.exit(1)
    #Construct the pair of zipfile pathnames
    file_root = name.split('-r')[0]
    zipname1 = "{0}-r{1}.zip".format(file_root, '1')
    zipname2 = "{0}-r{1}.zip".format(file_root, '2')
    #Construct the pathnames for output
    output = os.path.join(output_prefix, file_root)
    if os.path.isdir(output):
        shutil.rmtree(output)  # Delete previous output
    output_meta = os.path.join(output, 'META-INF')
    images_output = os.path.join(output, 'OPS', 'images')
    with zipfile.ZipFile(os.path.join(path, zipname1), 'r') as xml_zip:
        zip_dir = '{0}-r1'.format(file_root)
        xml = '/'.join([zip_dir, '{0}.xml'.format(file_root)])
        try:
            xml_zip.extract(xml)
        except KeyError:
            log.error('There is no item {0} in the zipfile'.format(xml))
            print('There is no item {0} in the zipfile'.format(xml))
            sys.exit(1)
        else:
            if not os.path.isdir(output_meta):
                os.makedirs(output_meta)
            article = Article(xml)
            shutil.copy(xml, os.path.join(output_meta))
            os.remove(xml)
            os.rmdir(zip_dir)
    with zipfile.ZipFile(os.path.join(path, zipname2), 'r') as image_zip:
        zip_dir = '{0}-r2'.format(file_root)
        for i in image_zip.namelist():
            if 'image_m' in i:
                image_zip.extract(i)
        if not os.path.isdir(images_output):
            os.makedirs(images_output)
        unzipped_images = os.path.join(zip_dir, 'images', 'image_m')
        for i in os.listdir(unzipped_images):
            shutil.copy(os.path.join(unzipped_images, i), images_output)
        shutil.rmtree(zip_dir)
    return article, file_root
