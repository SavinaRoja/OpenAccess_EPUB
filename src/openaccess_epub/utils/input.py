# -*- coding: utf-8 -*-
"""
The methods in this module all utilize their string argument to specify and
(optionally) download an input xml file. They all return the base name of their
input file; that is, the extension-less name of the file. These base names then
provide the basis for instantiating Article class objects and the naming of
output files.
"""

import openaccess_epub.utils
import urllib.request, urllib.parse, urllib.error
import sys
import os
import zipfile
import shutil
import logging

log = logging.getLogger('utils.input')


def plos_doi_to_xmlurl(doi_string):
    """
    Attempts to resolve a PLoS DOI into a URL path to the XML file.
    """
    #Create URL to request DOI resolution from http://dx.doi.org
    doi_url = 'http://dx.doi.org/{0}'.format(doi_string)
    log.debug('DOI URL: {0}'.format(doi_url))
    #Open the page, follow the redirect
    try:
        resolved_page = urllib.request.urlopen(doi_url)
    except urllib.error.URLError as err:
        print('Unable to resolve DOI URL, or could not connect')
        raise err
    else:
        #Given the redirection, attempt to shape new request for PLoS servers
        resolved_address = resolved_page.geturl()
        log.debug('DOI resolved to {0}'.format(resolved_address))
        parsed = urllib.parse.urlparse(resolved_address)
        xml_url = '{0}://{1}'.format(parsed.scheme, parsed.netloc)
        xml_url += '/article/fetchObjectAttachment.action?uri='
        xml_path = parsed.path.replace(':', '%3A').replace('/', '%2F')
        xml_path = xml_path.split('article%2F')[1]
        xml_url += '{0}{1}'.format(xml_path, '&representation=XML')
        log.debug('Shaped PLoS request for XML {0}'.format(xml_url))
        #Return this url to the calling function
        return xml_url


def get_file_root(full_path):
    """
    This method provides the standard mode of deriving the file root name from
    a given path to the file; excludes the file extension and all parent
    directories.
    """
    filename = os.path.split(full_path)[1]
    return os.path.splitext(filename)[0]


def local_input(xml_path, download=None):
    """
    
    This method accepts xml path data as an argument, instantiates the Article,
    and returns the two.
    
    """
    log.info('Local Input - {0}'.format(xml_path))
    return get_file_root(xml_path)


def doi_input(doi_string, download=True):
    """
    This method accepts a DOI string and attempts to download the appropriate
    xml file. If successful, it returns a path to that file along with an
    Article instance of that file. This works by requesting the correct page
    from http://dx.doi.org/ and then using publisher conventions to identify
    the article xml on that page.
    """
    log.info('DOI Input - {0}'.format(doi_string))
    if '10.1371' in doi_string:  # Corresponds to PLoS
        xml_url = plos_doi_to_xmlurl(doi_string)
    else:
        print('This publisher is not yet supported by OpenAccess_EPUB')
        sys.exit(1)
    return url_input(xml_url, download)


def url_input(url_string, download=True):
    """
    This method expects a direct URL link to an xml file. It will apply no
    modifications to the received URL string, so ensure good input.
    """
    log.info('URL Input - {0}'.format(url_string))
    try:
        open_xml = urllib.request.urlopen(url_string)
    except urllib.error.URLError as err:
        print('utils.input.url_input received a bad URL, or could not connect')
        raise err
    else:
        #Employ a quick check on the mimetype of the link
        if not open_xml.headers['Content-Type'] == 'text/xml':
            print('URL request does not appear to be XML')
            sys.exit(1)  # Nonzero value for "abnormal" termination
        filename = open_xml.headers['Content-Disposition'].split('\"')[1]
        if download:
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
        return get_file_root(filename)


def frontiersZipInput(zip_path, output_prefix, download=None):
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
    return file_root
