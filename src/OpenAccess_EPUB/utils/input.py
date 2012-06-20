"""
This collection of utility functions are all related to passing input documents
to the OpenAccess_EPUB main function. They are all required to return the same
two things: the path to a local XML file, and an instance of Article made by
passing that file to the class.
"""

from OpenAccess_EPUB.article import Article
import urllib2
import urlparse
import os.path
import sys


def localInput(xml_path):
    """
    This method accepts xml path data as an argument, instantiates the Article,
    and returns the two.
    """
    art = Article(xml_path)
    return xml_path, art


def doiInput(doi_string):
    """
    This method accepts a DOI string and attempts to download the appropriate
    xml file. If successful, it returns a path to that file along with an
    Article instance of that file. This works by requesting the correct page
    from http://dx.doi.org/ and then using publisher conventions to identify
    the article xml on that page.
    """
    pub_doi = {'10.1371': 'PLoS', '10.3389': 'Frontiers'}
    #A user might accidentally copy/paste the "doi:" part of a DOI
    if doi_string[:4]:
        doi_string = doi_string[4:]
    #Compose the URL to access at http://dx.doi.org
    doi_url = 'http://dx.doi.org/{0}'.format(doi_string)
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
        xml_path = filename
        return art, xml_path
    else:
        print('{0} is not supported for DOI Input'.format(publisher))
        sys.exit(1)


def urlInput(url_string):
    """
    This method accepts a URL as an input and attempts to download the
    appropriate xml file from that page. This method is highly dependent on
    publisher conventions and may not be appropriate for all pusblishers.
    """
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
            xml_path = filename
            return art, xml_path
    else:  # We don't support this input or publisher
        print('Invalid Link: Bad URL or unsupported publisher')
        print('Supported publishers are: {0}'.format(', '.join(support)))
        sys.exit(1)
