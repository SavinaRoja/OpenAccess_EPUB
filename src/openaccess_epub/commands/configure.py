# -*- coding: utf-8 -*-

"""
oaepub configure

Configure basic defaults for OpenAccess_EPUB conversion.

Usage:
  configure [--help | --version | --default | --dev | where]

Options:
  -h --help     Show this help message and exit
  -v --version  Show program version and exit
  -d --default  Set configuration to default and exit
  --dev         Set developer configuration and exit
"""

#Standard Library modules
import os
#import sys
import time

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
from openaccess_epub._version import __version__
import openaccess_epub
import openaccess_epub.utils

CWD = os.getcwd()

CONFIG_TEXT = '''# -*- coding: utf-8 -*-
#
# OpenAccess_EPUB configuration file, created by oaepub configure on
# {now}.
#
# OpenAccess_EPUB v.{oae-version} was detected at runtime
#
# The configurations made in this file define certain default actions and/or
# location values utilized by the OpenAccess_EPUB conversion tools. These are
# broadly defined options, and should have the same meaning within the context
# of distinct oaepub subcommands. Note that commandline options passed to the
# oaepub commands will always take precedence over these defaults.

# TAKE NOTE: The Meaning of Absolute or Relative Paths
# Some options require absolute path locations. Others require relative path
# locations. While even others may allow either. An absolute path is *constant*
# and unchanging (it will start with a slash in unix style, or a drive-letter
# and a backslash in Windows). A relative path is *relative* to an INPUT and
# will be evaluated at runtime. For instance, if INPUT is /foo/bar and the
# relative path option is ./spam, then the result is /foo/bar/spam

# Python uses back slashes, "\\", as escape characters so if you are on Windows
# make sure to use "\\\\" for every back slash in a path. You can also use unix-
# style paths with forward slashes "/", this should work on all platforms.

# oaepub needs to be able to reliably find this config file; it will always be
# located in the directory returned by openaccess_epub.utils.cache_location().
# This directory is:

cache_location = '{cache-location}'

# -- Images Configuration -----------------------------------------------------
# OpenAccess_EPUB supports multiple means of moving images into EPUB files.
# The different methods are listed below according to first priority, a higher
# priority method will supersede a lower one.
#   Input-Relative : Looks for images under directories relative to the input
#   Image Cache : Looks for images in the cache, saves time to avoid fetching
#   Image Fetching : If supported, download the images from the Internet

# -- Input-Relative Options --
# A list of paths relative to the input from which to pull images
# The program will check each of these locations and copy the images from
# the first one it finds.
# Note: OpenAccess_EPUB supports the use of wildcard (*) matching and this can
# be a very useful feature. If an input file is named "journal.pcbi.1002904.xml"
# and the following list contains the string 'images-*', then a directory named
# "images-journal.pcbi.1002904" will be found by OpenAccess_EPUB
input_relative_images = [{input-relative-images}]

# A Boolean toggle for whether or not to use Input-Relative images
use_input_relative_images = {use-input-relative-images}

# -- Image Cache Options --
# An absolute path to the image cache top level directory
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
# publishers or those wishing to distribute EPUB output. EpubCheck is a separate
# program which you must install on your system for OpenAccess_EPUB to be able
# to call upon it. Use the following variable to define where OpenAccess_EPUB
# can find the .jar file for EpubCheck. Requires Java.
epubcheck_jarfile = '{epubcheck-jarfile}'

disable_epubcheck=False

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
            openaccess_epub.utils.evaluate_relative_path(relative=user_path)
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
    Interactive prompts that receive paths will be coerced to unix-style with
    forward slashes by this function.
    """
    return input_path.replace('\\', '/')


def configure(default=None, dev=None):
    """
    The inner control loops for user interaction during quickstart
    configuration.
    """
    cache_loc = openaccess_epub.utils.cache_location()
    config_loc = openaccess_epub.utils.config_location()

    #Make the cache directory
    openaccess_epub.utils.mkdir_p(cache_loc)

    defaults = {'now': time.asctime(),
                'oae-version': openaccess_epub.__version__,
                'cache-location': unix_path_coercion(cache_loc),
                'input-relative-images': 'images-*',
                'use-input-relative-images': 'y',
                'image-cache': os.path.join(cache_loc, 'img_cache'),
                'use-image-cache': 'n',
                'use-image-fetching': 'y',
                'default-output': '.',
                'input-relative-css': '.',
                'epubcheck-jarfile': os.path.join(cache_loc,
                                                 'epubcheck-3.0',
                                                 'epubcheck-3.0.jar')}

    if default or dev:  # Skip interactive and apply defaults
        #Pass through the validation/modification steps
        if dev:  # The only current difference between dev and default
            defaults['use-image-cache'] = 'y'
        defaults['input-relative-images'] = list_opts(defaults['input-relative-images'])
        defaults['use-input-relative-images'] = boolean(defaults['use-input-relative-images'])
        defaults['image-cache'] = absolute_path(defaults['image-cache'])
        defaults['use-image-cache'] = boolean(defaults['use-image-cache'])
        defaults['use-image-fetching'] = boolean(defaults['use-image-fetching'])
        defaults['default-output'] = nonempty(defaults['default-output'])
        defaults['input-relative-css'] = nonempty(defaults['input-relative-css'])
        defaults['epubcheck-jarfile'] = absolute_path(defaults['epubcheck-jarfile'])
        config = config_formatter(CONFIG_TEXT, defaults)

        with open(config_loc, 'wb') as conf_out:
            conf_out.write(bytes(config, 'UTF-8'))
        print('The config file has been written to {0}'.format(config_loc))
        return

    config_dict = {'now': time.asctime(),
                   'oae-version': openaccess_epub.__version__,
                   'cache-location': unix_path_coercion(cache_loc)}

    print('''\nWelcome to the interactive configuration for OpenAccess_EPUB''')
    print('''
Please enter values for the following settings. To accept the default value
for the settings, shown in brackets, just push Enter.

-------------------------------------------------------------------------------\
''')
    print('''
OpenAccess_EPUB defines a default cache location for the storage of various
data (and the global config.py file), this location is:\n\n{0}
'''.format(cache_loc))

    input('Press Enter to start...')

    #Image Configuration
    print('''
 -- Configure Image Behavior --

When OpenAccess_EPUB is executed using the oaepub script, it can find the
images for the input articles using the following strategies (in order of
preference):

 Input-Relative: a path relative to the input file
 Cached Images: locate the images in a cache
 Fetched Online: attempts to download from the Internet (may fail)

We'll configure some values for each of these, and you\'ll also have the option
to turn them off.''')
    #Input-relative image details
    print('''
Where should OpenAccess_EPUB look for images relative to the input file?
A star "*" may be used as a wildcard to match the name of the input file.
Multiple path values may be specified if separated by commas.''')
    user_prompt(config_dict, 'input-relative-images', 'Input-relative images?:',
                default=defaults['input-relative-images'], validator=list_opts)
    print('''
Should OpenAccess_EPUB look for images relative to the input file by default?\
''')
    user_prompt(config_dict, 'use-input-relative-images',
                'Use input-relative images?: (Y/n)',
                default=defaults['use-input-relative-images'],
                validator=boolean)
    #Image cache details
    print('''
Where should OpenAccess_EPUB place the image cache?''')
    user_prompt(config_dict, 'image-cache', 'Image cache?:',
                default=defaults['image-cache'],
                validator=absolute_path)
    print('''
Should OpenAccess_EPUB use the image cache by default? This feature is intended
for developers and testers without local access to the image files and will
consume extra disk space for storage.''')
    user_prompt(config_dict, 'use-image-cache', 'Use image cache?: (y/N)',
                default=defaults['use-image-cache'],
                validator=boolean)
    #Image fetching online details
    print('''
Should OpenAccess_EPUB attempt to download the images from the Internet? This
is not supported for all publishers and not 100% guaranteed to succeed, you may
need to download them manually if this does not work.''')
    user_prompt(config_dict, 'use-image-fetching', 'Attempt image download?: (Y/n)',
                default=defaults['use-image-fetching'],
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
                default=defaults['default-output'],
                validator=nonempty)
    print('''
 -- Configure CSS Behavior --

ePub files use CSS for improved styling, and ePub-readers must support a basic
subset of CSS functions. OpenAccess_EPUB provides a default CSS file, but a
manual one may be supplied, relative to the input. Please define an
appropriate input-relative path.''')
    user_prompt(config_dict, 'input-relative-css', 'Input-relative CSS path?:',
                default=defaults['input-relative-css'],
                validator=nonempty)
    print('''
 -- Configure EpubCheck --

EpubCheck is a program written and maintained by the IDPF as a tool to validate
ePub. In order to use it, your system must have Java installed and it is
recommended to use the latest version. Downloads of this program are found here:

https://github.com/IDPF/epubcheck/releases

Once you have downloaded the zip file for the program, unzip the archive and
write a path to the .jar file here.''')
    user_prompt(config_dict, 'epubcheck-jarfile', 'Absolute path to epubcheck?:',
                default=defaults['epubcheck-jarfile'], validator=absolute_path)
    #Write the config.py file
    config = config_formatter(CONFIG_TEXT, config_dict)
    with open(config_loc, 'wb') as conf_out:
        conf_out.write(bytes(config, 'UTF-8'))
    print('''
Done configuring OpenAccess_EPUB!''')


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB v.' + __version__,
                  options_first=True)

    if args['where']:
        print(openaccess_epub.utils.config_location())
        return

    try:
        configure(default=args['--default'], dev=args['--dev'])
    except (KeyboardInterrupt, EOFError):
        print('\n[Interrupted.]')
        return

if __name__ == '__main__':
    main()

