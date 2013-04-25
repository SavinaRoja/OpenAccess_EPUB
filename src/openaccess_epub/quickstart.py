# -*- coding: utf-8 -*-
"""
openaccess_epub.quickstart

Used for configuring an installation of OpenAccess_EPUB
"""

from openaccess_epub.utils import cache_location
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
# The script detected OpenAccess_EPUB v.{oae-version} at that time.
#
# At this point in time, all possible values for configuration are represented
# in this file. Suggested defaults exist for all values, but each may receive
# alternatives from the user. To reconfigure or reset to defaults, simply run
# oae-quickstart again.
#
# Please note that some of the configurations in this file may be overridden by
# flags passed manually to the oaepub script.

import os.path
import sys
import logging

# oaepub needs to be able to reliably find this config file; it will always be
# located in the directory returned by openaccess_epub.utils.cache_location().
# This directory is:

cache_location = '{cache-location}'


'''

class ValidationError(Exception):
    """Raised error for invalid user input"""

def nonempty(x):
    if not x:
        raise ValidationError('Please enter some text.')
    return x

def boolean(x):
    if x.upper() not in ('Y', 'YES', 'N', 'NO'):
        raise ValidationError("Please enter either 'y' or 'n'.")
    return x.upper() in ('Y', 'YES')

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
    Places the config dictionary values into the appropriate keynamed areas in
    the config text.
    """
    return(config_string.format(**config_dict))

def inner_main(args):
    """
    The inner control loops for user interaction during quickstart
    configuration.
    """

    default_config={'now': time.asctime(),
                    'oae-version': OAE_VERSION,
                    'cache-location': CACHE_LOCATION,
                    'input-relative': 'images',
                    'use-input-relative': 'y',
                    'execution-relative': 'images',
                    'use-execution-relative': 'n',
                    'image-cache': os.path.join(CACHE_LOCATION, 'img_cache'),
                    'use-image-cache': 'n',
                    'use-image-fetching': 'y',
                    'default-output': '.{0}'.format(os.sep)}

    if args[-1] == '-d':  # Use all default options flag
        config = config_formatter(CONFIG_TEXT, default_config)
        with open(os.path.join(CACHE_LOCATION, 'config.py'), 'wb') as conf_out:
            conf_out.write(bytes(config, 'UTF-8'))
        return

    config_dict = {'now': time.asctime(),
                   'oae-version': OAE_VERSION,
                   'cache-location': CACHE_LOCATION}

    print('\nWelcome to the quickstart configuration for OpenAccess_EPUB')
    print('''
Please enter values for the following settings. To accept the default value
for the settings, shown in brackets, just push Enter.
''')

    print('''\
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
 Execution-Relative: a path relative to the directory of script execution
 Cached Images: locate the images in a cache
 Fetched Online: attempts to download from the Internet (may fail)

We'll configure some values for each of these, and you\'ll also have the option
to turn them off.''')
    #Input-relative image details
    print('''
Where should OpenAccess_EPUB look for images relative to the input file?
Multiple path values may be specified if separated by commas.''')
    user_prompt(config_dict, 'input-relative', 'Input-relative images: path?',
                default=default_config['input-relative'], validator=nonempty)
    print('''
Should OpenAccess_EPUB look for images relative to the input file by default?\
''')
    user_prompt(config_dict, 'use-input-relative',
                'Use input-relative images: (Y/n)',
                default=default_config['use-input-relative'],
                validator=boolean)
    #Execution-relative image details
    print('''
Where should OpenAccess_EPUB look for images relative to the execution path?
Multiple path values may be specified if separated by commas.''')
    user_prompt(config_dict, 'execution-relative',
                'Execution-relative images: path?',
                default=default_config['execution-relative'],
                validator=nonempty)
    print('''
Should OpenAccess_EPUB look for images relative to the execution path by
default?''')
    user_prompt(config_dict, 'use-execution-relative',
                'Use execution-relative images: (Y/n)',
                default=default_config['use-execution-relative'],
                validator=boolean)
    #Image cache details
    print('''
Where should OpenAccess_EPUB place the image cache?''')
    user_prompt(config_dict, 'image-cache', 'Image cache?: absolute path',
                default=default_config['image-cache'],
                validator=nonempty)
    print('''
Should OpenAccess_EPUB use the image cache by default? This feature is intended
for developers and testers without local access to the image files and will
consume extra disk space for storage.''')
    user_prompt(config_dict, 'use-image-cache', 'Use image cache (y/N)',
                default=default_config['use-image-cache'],
                validator=boolean)
    #Image fetching online details
    print('''
Should OpenAccess_EPUB attempt to download the images from the Internet, this
is not supported for all publishers and not 100% guaranteed to succeed.''')
    user_prompt(config_dict, 'use-image-fetching', 'Attempt image download (Y/n)',
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
''')


    for key in config_dict.keys():
        print('{0}: {1}'.format(key, config_dict[key]))

def main(argv=sys.argv):
    try:
        return inner_main(argv)
    except (KeyboardInterrupt, EOFError):
        print('\n[Interrupted.]')
        return
