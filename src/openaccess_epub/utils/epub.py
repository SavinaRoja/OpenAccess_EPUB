# -*- coding: utf-8 -*-
"""
Utilities related to the making and managing of EPUB files
"""
#Standard Library modules
import logging
import os
import zipfile

#Non-Standard Library modules

#OpenAccess_EPUB modules
import openaccess_epub
from openaccess_epub.utils.css import DEFAULT_CSS
from openaccess_epub.navigation import Navigation
from openaccess_epub.package import Package
import openaccess_epub.ops

log = logging.getLogger('openaccess_epub.utils.epub')


def make_EPUB(parsed_article,
              output_directory,
              input_path,
              image_directory,
              config_module=None,
              epub_version=None,
              batch=False):
    """
    Standard workflow for creating an EPUB document.

    make_EPUB is used to produce an EPUB file from a parsed article. In addition
    to the article it also requires a path to the appropriate image directory
    which it will insert into the EPUB file, as well the output directory
    location for the EPUB file.

    Parameters
    ----------
    article : openaccess_epub.article.Article instance
        `article` is an Article instance for the XML document to be converted to
        EPUB.
    output_directory : str
        `output_directory` is a string path to the directory in which the EPUB
        will be produced. The name of the directory will be used as the EPUB's
        filename.
    input_path : str
        `input_path` is a string absolute path to the input XML file, used to
        locate input-relative images.
    image_directory : str
        `image_directory` is a string path indicating an explicit image
        directory. If supplied, other image input methods will not be used.
    config_module : config module, optional
        `config_module` is a pre-loaded config module for OpenAccess_EPUB; if
        not used then this function will load the global config file. Might be
        useful in certain cases to dynamically alter configuration.
    epub_version : {None, 2, 3}
        `epub_version` dictates which version of EPUB to be created. An error
        will be raised if the specified version is not supported for the
        publisher. If left to the default, the created version will defer to the
        publisher default version.
    batch : bool, optional
        `batch` indicates that batch creation is being used (such as with the
        `oaepub batch` command). In this case, directory conflicts will be
        automatically resolved (in favor of keeping previous data, skipping
        creation of EPUB).

    Returns False in the case of a fatal error, True if successful.
    """
    #command_log.info('Creating {0}.epub'.format(output_directory))
    if config_module is None:
        config_module = openaccess_epub.utils.load_config_module()

    if epub_version not in (None, 2, 3):
        log.error('Invalid EPUB version: {0}'.format(epub_version))
        raise ValueError('Invalid EPUB version. Should be 2 or 3')

    if epub_version is None:
        epub_version = parsed_article.publisher.epub_default

    #Handle directory output conflicts
    if os.path.isdir(output_directory):
        if batch:  # No user prompt, default to protect previous data
            log.error('Directory conflict during batch conversion, skipping.')
            return False
        else:  # User prompting
            openaccess_epub.utils.dir_exists(output_directory)
    else:
        try:
            os.makedirs(output_directory)
        except OSError as err:
            if err.errno != 17:
                log.exception('Unable to recursively create output directories')

    #Copy over the basic epub directory
    make_epub_base(output_directory)

    #Get the images, if possible, fail gracefully if not
    success = openaccess_epub.utils.images.get_images(output_directory,
                                                      image_directory,
                                                      input_path,
                                                      config_module,
                                                      parsed_article)
    if not success:
        log.critical('Images for the article were not located! Aborting!')
        return False

    #Instantiate Navigation and Package
    epub_nav = Navigation()
    epub_package = Package()

    #Process the article for navigation and package info
    epub_nav.process(parsed_article)
    epub_package.process(parsed_article)

    #Render the content using publisher-specific methods
    parsed_article.publisher.render_content(output_directory, epub_version)
    if epub_version == 2:
        epub_nav.render_EPUB2(output_directory)
        epub_package.render_EPUB2(output_directory)
    elif epub_version == 3:
        epub_nav.render_EPUB3(output_directory)
        epub_package.render_EPUB3(output_directory)

    #Zip the directory into EPUB
    epub_zip(output_directory)

    return True


def make_epub_base(location):
    """
    Creates the base structure for an EPUB file in a specified location.

    This function creates constant components for the structure of the EPUB in
    a specified directory location.

    Parameters
    ----------
    location : str
        A path string to a local directory in which the EPUB is to be built
    """
    log.info('Making EPUB base files in {0}'.format(location))
    with open(os.path.join(location, 'mimetype'), 'w') as out:  # mimetype file
        out.write('application/epub+zip')

    #Create OPS and META-INF directorys
    os.mkdir(os.path.join(location, 'META-INF'))
    os.mkdir(os.path.join(location, 'EPUB'))
    os.mkdir(os.path.join(location, 'EPUB', 'css'))

    with open(os.path.join(location, 'META-INF', 'container.xml'), 'w') as out:
        out.write('''\
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>''')

    with open(os.path.join(location, 'EPUB', 'css', 'default.css') ,'wb') as out:
        out.write(bytes(DEFAULT_CSS, 'UTF-8'))


def epub_zip(outdirect):
    """
    Zips up the input file directory into an EPUB file.
    """

    def recursive_zip(zipf, directory, folder=None):
        if folder is None:
            folder = ''
        for item in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, item)):
                zipf.write(os.path.join(directory, item),
                           os.path.join(directory, item))
            elif os.path.isdir(os.path.join(directory, item)):
                recursive_zip(zipf, os.path.join(directory, item),
                              os.path.join(folder, item))

    log.info('Zipping up the directory {0}'.format(outdirect))
    epub_filename = outdirect + '.epub'
    epub = zipfile.ZipFile(epub_filename, 'w')
    current_dir = os.getcwd()
    os.chdir(outdirect)
    epub.write('mimetype')
    log.info('Recursively zipping META-INF and OPS')
    for item in os.listdir('.'):
        if item == 'mimetype':
            continue
        recursive_zip(epub, item)
    os.chdir(current_dir)
    epub.close()