# -*- coding: utf-8 -*-
"""
OpenAccess_EPUB utilities for logging.
"""

import logging
import sys

logger = logging.getLogger('openaccess_epub.utils.logs')

STANDARD_FORMAT = '%(name)s - %(levelname)s - %(message)s'
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


def config_logging(log_to, log_level, log_echo, echo_level='info'):
    """
    Configures and generates a Logger object, 'openaccess_epub' based on common
    parameters used for console script execution in OpenAccess_EPUB.

    These parameters are:
      log_to
          A filename location for logging. If False, no log file will be used
      log_level
          Logging level, one of: 'debug', 'info', 'warning', 'error', 'critical'
      log_echo
          Will configure Logger to print to console as well if True
      echo_level
          Level of console printed logging if log_echo is True. Default : 'info'

    This function assumes it will only be called when logging is desired; it
    should not be called if an option such as '--no-log' is used.
    """

    log_level = get_level(log_level)
    echo_level = get_level(echo_level)

    log = logging.getLogger('openaccess_epub')
    log.setLevel(log_level)
    formatter = logging.Formatter(STANDARD_FORMAT)
    if log_to:
        fh = logging.FileHandler(filename=log_to)
        fh.setFormatter(formatter)
        log.addHandler(fh)
    #Add on the console StreamHandler if we are echoing to console
    if log_echo:
        sh_echo = logging.StreamHandler(sys.stdout)
        sh_echo.setLevel(echo_level)
        sh_echo.setFormatter(formatter)
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
