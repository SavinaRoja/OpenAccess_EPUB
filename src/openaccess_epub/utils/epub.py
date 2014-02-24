# -*- coding: utf-8 -*-
"""
Utilities related to the making and managing of EPUB files
"""
#Standard Library modules
import logging
import os
import shutil

#Non-Standard Library modules

#OpenAccess_EPUB modules
import openaccess_epub
import openaccess_epub.ncx
import openaccess_epub.opf
import openaccess_epub.ops

log = logging.getLogger('openaccess_epub.utils.epub')


def make_EPUB(parsed_article,
              output_directory,
              input_path,
              image_directory,
              config_module=None,
              batch=False):
    """
    make_EPUB is used to produce an EPUB file from a parsed article. In addition
    to the article it also requires a path to the appropriate image directory
    which it will insert into the EPUB file, as well the output directory
    location for the EPUB file.

    Parameters:
      article
          An Article object instance
      output_directory
          A directory path where the EPUB will be produced. The EPUB filename
          itself will always be
      input_path
          The absolute path to the input XML
      image_directory
          An explicitly indicated image directory, if used it will override the
          other image methods.
      config_module=None
          Allows for the injection of a modified or pre-loaded config module. If
          not specified, make_EPUB will load the config file

    Returns False in the case of a fatal error, True if successful.
    """
    #command_log.info('Creating {0}.epub'.format(output_directory))
    if config_module is None:
        config_module = openaccess_epub.utils.load_config_module()

    #Handle directory output conflicts
    if os.path.isdir(output_directory):
        if batch:  # No user prompt, default to protect previous data
            log.error('Directory conflict during batch conversion, skipping.')
            return False
        else:  # User prompting
            openaccess_epub.utils.dir_exists(output_directory)
    else:
        try:
            os.makedirs(os.path.dirname(output_directory))
        except OSError as err:
            if err.errno != 17:
                log.exception('Unable to recursively create output directories')

    #Copy over the basic epub directory
    base_epub = openaccess_epub.utils.base_epub_location()
    if not os.path.isdir(base_epub):
        openaccess_epub.utils.make_epub_base()
    shutil.copytree(base_epub, output_directory)

    DOI = parsed_article.doi

    #Get the images, if possible, fail gracefully if not
    success = openaccess_epub.utils.images.get_images(output_directory,
                                                      image_directory,
                                                      input_path,
                                                      config_module,
                                                      parsed_article)
    if not success:
        log.critical('Images for the article were not located! Aborting!')
        return False

    epub_toc = openaccess_epub.ncx.NCX(openaccess_epub.__version__,
                                       output_directory)
    epub_opf = openaccess_epub.opf.OPF(output_directory,
                                       collection_mode=False)

    epub_toc.take_article(parsed_article)
    epub_opf.take_article(parsed_article)

    #Split now based on the publisher for OPS processing
    if DOI.split('/')[0] == '10.1371':  # PLoS
        epub_ops = openaccess_epub.ops.OPSPLoS(parsed_article,
                                               output_directory)
    elif DOI.split('/')[0] == '10.3389':  # Frontiers
        epub_ops = openaccess_epub.ops.OPSFrontiers(parsed_article,
                                                    output_directory)

    #Now we do the additional file writing
    epub_toc.write()
    epub_opf.write()

    #Zip the directory into EPUB
    openaccess_epub.utils.epub_zip(output_directory)

    return True
