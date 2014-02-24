# -*- coding: utf-8 -*-
"""
OpenAccess_EPUB utilities for logging.
"""

import logging
import sys

logger = logging.getLogger('openaccess_epub.utils.logs')

STANDARD_FORMAT = '%(name)s [%(levelname)s] %(message)s'
MESSAGE_ONLY_FORMAT = '%(message)s'


def get_level(level_string):
    """
    Returns an appropriate logging level integer from a string name
    """
    levels = {'debug': logging.DEBUG, 'info': logging.INFO,
              'warning': logging.WARNING, 'error': logging.ERROR,
              'critical': logging.CRITICAL}
    try:
        level = levels[level_string.lower()]
    except KeyError:
        sys.exit('{0} is not a recognized logging level'.format(level_string))
    else:
        return level


def null_logging():
    """
    Configures the Logger for 'openaccess_epub' to do nothing
    """
    log = logging.getLogger('openaccess_epub')
    log.addHandler(logging.NullHandler())


def config_logging(no_log_file, log_to, log_level, silent, verbosity):
    """
    Configures and generates a Logger object, 'openaccess_epub' based on common
    parameters used for console interface script execution in OpenAccess_EPUB.

    These parameters are:
      no_log_file
          Boolean. Disables logging to file. If set to True, log_to and
          log_level become irrelevant.
      log_to
          A string name indicating a file path for logging.
      log_level
          Logging level, one of: 'debug', 'info', 'warning', 'error', 'critical'
      silent
          Boolean
      verbosity
          Console logging level, one of: 'debug', 'info', 'warning', 'error',
          'critical

    This method currently only configures a console StreamHandler with a
    message-only Formatter.
    """

    log_level = get_level(log_level)
    console_level = get_level(verbosity)

    #We want to configure our openaccess_epub as the parent log
    log = logging.getLogger('openaccess_epub')
    log.setLevel(logging.DEBUG)  # Don't filter at the log level
    standard = logging.Formatter(STANDARD_FORMAT)
    message_only = logging.Formatter(MESSAGE_ONLY_FORMAT)

    #Only add FileHandler IF it's allowed AND we have a name for it
    if not no_log_file and log_to is not None:
        fh = logging.FileHandler(filename=log_to)
        fh.setLevel(log_level)
        fh.setFormatter(standard)
        log.addHandler(fh)

    #Add on the console StreamHandler at verbosity level if silent not set
    if not silent:
        sh_echo = logging.StreamHandler(sys.stdout)
        sh_echo.setLevel(console_level)
        sh_echo.setFormatter(message_only)
        log.addHandler(sh_echo)


def replace_filehandler(logname, new_file, level=None, frmt=None):
    """
    This utility function will remove a previous Logger FileHandler, if one
    exists, and add a new filehandler.

    Parameters:
      logname
          The name of the log to reconfigure, 'openaccess_epub' for example
      new_file
          The file location for the new FileHandler
      level
          Optional. Level of FileHandler logging, if not used then the new
          FileHandler will have the same level as the old. Pass in name strings,
          'INFO' for example
      frmt
          Optional string format of Formatter for the FileHandler, if not used
          then the new FileHandler will inherit the Formatter of the old, pass
          in format strings, '%(message)s' for example

    It is best practice to use the optional level and frmt arguments to account
    for the case where a previous FileHandler does not exist. In the case that
    they are not used and a previous FileHandler is not found, then the level
    will be set logging.DEBUG and the frmt will be set to
    openaccess_epub.utils.logs.STANDARD_FORMAT as a matter of safety.
    """
    #Call up the Logger to get reconfigured
    log = logging.getLogger(logname)

    #Set up defaults and whether explicit for level
    if level is not None:
        level = get_level(level)
        explicit_level = True
    else:
        level = logging.DEBUG
        explicit_level = False

    #Set up defaults and whether explicit for frmt
    if frmt is not None:
        frmt = logging.Formatter(frmt)
        explicit_frmt = True
    else:
        frmt = logging.Formatter(STANDARD_FORMAT)
        explicit_frmt = False

    #Look for a FileHandler to replace, set level and frmt if not explicit
    old_filehandler = None
    for handler in log.handlers:
        #I think this is an effective method of detecting FileHandler
        if type(handler) == logging.FileHandler:
            old_filehandler = handler
            if not explicit_level:
                level = handler.level
            if not explicit_frmt:
                frmt = handler.formatter
            break

    #Set up the new FileHandler
    new_filehandler = logging.FileHandler(new_file)
    new_filehandler.setLevel(level)
    new_filehandler.setFormatter(frmt)

    #Add the new FileHandler
    log.addHandler(new_filehandler)

    #Remove the old FileHandler if we found one
    if old_filehandler is not None:
        old_filehandler.close()
        log.removeHandler(old_filehandler)
