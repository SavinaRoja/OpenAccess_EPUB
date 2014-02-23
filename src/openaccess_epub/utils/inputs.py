# -*- coding: utf-8 -*-
"""
The methods in this module all utilize their string argument to specify and
(optionally) download an input xml file. They all return the base name of their
input file; that is, the extension-less name of the file. These base names then
provide the basis for instantiating Article class objects and the naming of
output files.
"""

import openaccess_epub.utils
import urllib.request
import urllib.parse
import urllib.error
import sys
import os
import zipfile
import shutil
import logging

log = logging.getLogger('openaccess_epub.utils.input')


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


def doi_input(doi_string, download=True):
    """
    This method accepts a DOI string and attempts to download the appropriate
    xml file. If successful, it returns a path to that file. As with all URL
    input types, the success of this method depends on supporting per-publisher
    conventions and will fail on unsupported publishers
    """
    log.debug('DOI Input - {0}'.format(doi_string))
    doi_string = doi_string[4:]
    if '10.1371' in doi_string:  # Corresponds to PLoS
        log.debug('DOI string shows PLoS')
        xml_url = plos_doi_to_xmlurl(doi_string)
    else:
        log.critical('DOI input for this publisher is not supported')
        sys.exit('This publisher is not yet supported by OpenAccess_EPUB')
    return url_input(xml_url, download)


def url_input(url_string, download=True):
    """
    This method expects a direct URL link to an xml file. It will apply no
    modifications to the received URL string, so ensure good input.
    """
    log.debug('URL Input - {0}'.format(url_string))
    try:
        open_xml = urllib.request.urlopen(url_string)
    except urllib.error.URLError as err:
        print('utils.input.url_input received a bad URL, or could not connect')
        raise err
    else:
        #Employ a quick check on the mimetype of the link
        if not open_xml.headers['Content-Type'] == 'text/xml':
            sys.exit('URL request does not appear to be XML')
        filename = open_xml.headers['Content-Disposition'].split('\"')[1]
        if download:
            with open(filename, 'wb') as xml_file:
                xml_file.write(open_xml.read())
        return openaccess_epub.utils.file_root_name(filename)


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
            log.critical('There is no item {0} in the zipfile'.format(xml))
            sys.exit('There is no item {0} in the zipfile'.format(xml))
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
