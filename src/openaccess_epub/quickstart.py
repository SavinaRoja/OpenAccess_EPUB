# -*- coding: utf-8 -*-
"""
openaccess_epub.quickstart

Used for configuring an installation of OpenAccess_EPUB
"""

from openaccess_epub.utils import cache_location, evaluate_relative_path, \
     mkdir_p
from openaccess_epub import __version__ as OAE_VERSION
import os
import sys
import time

LOCAL_DIR = os.getcwd()
CACHE_LOCATION = cache_location()

CONFIG_TEXT='''# -*- coding: utf-8 -*-
#
# OpenAccess_EPUB configuration file, created by oae-quickstart on
# {now}.
#
# The script detected OpenAccess_EPUB v.{oae-version}
#
# At this point in time, all possible values for configuration are represented
# in this file. Suggested defaults exist for all values, but each may receive
# alternatives from the user. To reconfigure, simply run oae-quickstart again.
# To quickly reset all values to default, run oae-quickstart -d
#
# Please note that some of the configurations in this file may be overridden by
# flags passed manually to the oaepub script.

import os
import sys
import logging

quickstart_version = '0.0.5'

# Python uses back slashes, "\\", as escape characters so if you are on Windows
# make sure to use "\\\\" for every back slash in a path. You can also use unix-
# style paths with forward slashes "/", this should work on all platforms.

# oaepub needs to be able to reliably find this config file; it will always be
# located in the directory returned by openaccess_epub.utils.cache_location().
# This directory is:

cache_location = '{cache-location}'

# -- Images Configuration -----------------------------------------------------
# OpenAccess_EPUB supports multiple means of moving images into ePub files.
# The different methods are listed below according to first priority, a higher
# priority method will supersede a lower one.
#   Input-Relative : Looks for images under directories relative to the input
#   Image Cache : Looks for images in the cache, saves time to avoid fetching
#   Image Fetching : If supported, download the images from the Internet

# -- Input-Relative Options --
# A list of paths relative to the input from which to pull images
input_relative_images = [{input-relative-images}]

# A Boolean toggle for whether or not to use Input-Relative images
use_input_relative_images = {use-input-relative-images}

# -- Image Cache Options --
# An absolute path to the image cache
image_cache = '{image-cache}'

# A Boolean toggle for whether or not to use the Image Cache
use_image_cache = {use-image-cache}

# -- Image Fetching Options --
# A Boolean toggle for whether or not to use Image Fetching
use_image_fetching = {use-image-fetching}

# -- Output Configuration -----------------------------------------------------
# OpenAccess_EPUB can place the output in the desired location. A relative path
# will be interpreted as relative to the input, and an absolute path will serve
# as a fixed output directory.
default_output = '{default-output}'

# -- CSS Configuration --------------------------------------------------------
# OpenAccess_EPUB can utilize a CSS file relative to the input if configured,
# it will be employed instead of the default CSS if found. This variable sets
# where OpenAccess_EPUB will look relative to the input.
input_relative_css = '{input-relative-css}'

# -- EpubCheck Configuration --------------------------------------------------
# All output SHOULD be passed to EpubCheck, this is especially true for
# publishers or those wishing to distribute ePub output. EpubCheck is not a
# part of the default workflow of OpenAccess_EPUB in Batch Mode, relying
# on the user to separately execute EpubCheck, this is due to the large time
# commitment it takes to run EpubCheck on a great quantity of files.
# Use the following variable to define where the jar file for EpubCheck is
epubcheck = '{epubcheck}'

'''

class ValidationError(Exception):
    """Raised error for invalid user input"""

def nonempty(x):
    if not x:
        raise ValidationError('Please enter some text.')
    return unix_path_coercion(x)

def absolute_path(user_path):
    """
    Some paths must be made absolute, this will attempt to convert them.
    """
    if os.path.abspath(user_path):
        return unix_path_coercion(user_path)
    else:
        try:
            evaluate_relative_path(LOCAL_DIR, working_path)
        except:
            raise ValidationError('This path could not be rendered as absolute')

def boolean(x):
    if x.upper() not in ('Y', 'YES', 'N', 'NO'):
        raise ValidationError("Please enter either 'y' or 'n'.")
    return x.upper() in ('Y', 'YES')

def list_opts(x):
    try:
        return ', '.join(['\'' + unix_path_coercion(opt.strip()) + '\'' for opt in x.split(',')])
    except:
        raise ValidationError('Could not understand your input')

def user_prompt(config_dict, key, text, default=None, validator=nonempty):
    while True:
        if default:
            prompt = '> {0} [{1}]: '.format(text, default)
        else:
            prompt = '> {0}: '.format(text)
        user_inp = input(prompt)
        if default and not user_inp:
            user_inp = default
        try:
            user_inp = validator(user_inp)
        except ValidationError as error:
            print('* ' + str(error))
            continue
        break
    config_dict[key] = user_inp

def config_formatter(config_string, config_dict):
    """
    Places the config dictionary values into the appropriate key-named areas in
    the config text.
    """
    return(config_string.format(**config_dict))

def unix_path_coercion(input_path):
    """
    The prompts during the quickstart run that receive paths will be coerced to
    use unix-style forward slashes with this function.
    """
    return input_path.replace('\\', '/')

def inner_main(args):
    """
    The inner control loops for user interaction during quickstart
    configuration.
    """

    #Make the cache directory
    mkdir_p(CACHE_LOCATION)

    default_config={'now': time.asctime(),
                    'oae-version': OAE_VERSION,
                    'cache-location': unix_path_coercion(CACHE_LOCATION),
                    'input-relative-images': 'images',
                    'use-input-relative-images': 'y',
                    'image-cache': os.path.join(CACHE_LOCATION, 'img_cache'),
                    'use-image-cache': 'n',
                    'use-image-fetching': 'y',
                    'default-output': '.',
                    'input-relative-css': '.',
                    'epubcheck': os.path.join(CACHE_LOCATION, 'epubcheck-3.0', 'epubcheck-3.0.jar')}

    if args[-1] == '-d':  # Use all default options flag
        #Pass through the validation/modification steps
        default_config['input-relative-images'] = list_opts(default_config['input-relative-images'])
        default_config['use-input-relative-images'] = boolean(default_config['use-input-relative-images'])
        default_config['image-cache'] = absolute_path(default_config['image-cache'])
        default_config['use-image-cache'] = boolean(default_config['use-image-cache'])
        default_config['use-image-fetching'] = boolean(default_config['use-image-fetching'])
        default_config['default-output'] = nonempty(default_config['default-output'])
        default_config['input-relative-css'] = nonempty(default_config['input-relative-css'])
        default_config['epubcheck'] = absolute_path(default_config['epubcheck'])
        config = config_formatter(CONFIG_TEXT, default_config)
        with open(os.path.join(CACHE_LOCATION, 'config.py'), 'wb') as conf_out:
            conf_out.write(bytes(config, 'UTF-8'))
        print('The config file has been written to {0}'.format(os.path.join(CACHE_LOCATION, 'config.py')))
        return

    config_dict = {'now': time.asctime(),
                   'oae-version': OAE_VERSION,
                   'cache-location': unix_path_coercion(CACHE_LOCATION)}

    print('\nWelcome to the quickstart configuration for OpenAccess_EPUB')
    print('''
Please enter values for the following settings. To accept the default value
for the settings, shown in brackets, just push Enter.

-------------------------------------------------------------------------------\
''')
    print('''
OpenAccess_EPUB defines a default cache location for the storage of various
data (and the global config.py file), this location is:\n\n{0}
'''.format(CACHE_LOCATION))

    input('Press Enter to start...')

    #Image Configuration
    print('''
 -- Configure Image Behavior --

When OpenAccess_EPUB is executed using the oaepub script, it can find the
images for the input articles according to the following strategies (in order
of preference):

 Input-Relative: a path relative to the input file
 Cached Images: locate the images in a cache
 Fetched Online: attempts to download from the Internet (may fail)

We'll configure some values for each of these, and you\'ll also have the option
to turn them off.''')
    #Input-relative image details
    print('''
Where should OpenAccess_EPUB look for images relative to the input file?
Multiple path values may be specified if separated by commas.''')
    user_prompt(config_dict, 'input-relative-images', 'Input-relative images?:',
                default=default_config['input-relative-images'], validator=list_opts)
    print('''
Should OpenAccess_EPUB look for images relative to the input file by default?\
''')
    user_prompt(config_dict, 'use-input-relative-images',
                'Use input-relative images?: (Y/n)',
                default=default_config['use-input-relative-images'],
                validator=boolean)
    #Image cache details
    print('''
Where should OpenAccess_EPUB place the image cache?''')
    user_prompt(config_dict, 'image-cache', 'Image cache?:',
                default=default_config['image-cache'],
                validator=absolute_path)
    print('''
Should OpenAccess_EPUB use the image cache by default? This feature is intended
for developers and testers without local access to the image files and will
consume extra disk space for storage.''')
    user_prompt(config_dict, 'use-image-cache', 'Use image cache?: (y/N)',
                default=default_config['use-image-cache'],
                validator=boolean)
    #Image fetching online details
    print('''
Should OpenAccess_EPUB attempt to download the images from the Internet? This
is not supported for all publishers and not 100% guaranteed to succeed, you may
need to download them manually if this does not work.''')
    user_prompt(config_dict, 'use-image-fetching', 'Attempt image download?: (Y/n)',
                default=default_config['use-image-fetching'],
                validator=boolean)
    #Output configuration
    print('''
 -- Configure Output Behavior --

OpenAccess_EPUB produces ePub and log files as output. The following options
will determine what is done with these.

Where should OpenAccess_EPUB place the output ePub and log files? If you supply
a relative path, the output path will be relative to the input; if you supply
an absolute path, the output will always be placed there. The default behavior
is to place them in the same directory as the input.''')
    user_prompt(config_dict, 'default-output', 'Output path?:',
                default=default_config['default-output'],
                validator=nonempty)
    print('''
 -- Configure CSS Behavior --

ePub files use CSS for improved styling, and ePub-readers must support a basic
subset of CSS functions. OpenAccess_EPUB provides a default CSS file, but a
manual one may be supplied, relative to the input. Please define an
appropriate input-relative path.''')
    user_prompt(config_dict, 'input-relative-css', 'Input-relative CSS path?:',
                default=default_config['input-relative-css'],
                validator=nonempty)
    print('''
 -- Configure EpubCheck --

EpubCheck is a program written and maintained by the IDPF as a tool to validate
ePub. In order to use it, your system must have Java installed and it is
recommended to use the latest version. The website for the program is here:

http://code.google.com/p/epubcheck/

Once you have downloaded the zip file for the program, unzip the archive and
write a path to the .jar file here.''')
    user_prompt(config_dict, 'epubcheck', 'Absolute path to epubcheck?:',
                default=default_config['epubcheck'], validator=absolute_path)
    #Write the config.py file
    config = config_formatter(CONFIG_TEXT, config_dict)
    with open(os.path.join(CACHE_LOCATION, 'config.py'), 'wb') as conf_out:
        conf_out.write(bytes(config, 'UTF-8'))
    print('''
Done configuring OpenAccess_EPUB!''')

def main(argv=sys.argv):
    try:
        return inner_main(argv)
    except (KeyboardInterrupt, EOFError):
        print('\n[Interrupted.]')
        return
