# -*- coding: utf-8 -*-
"""
OpenAccess_EPUB utilities for logging.
"""

import logging
import sys

#These are strings for
STANDARD_FORMAT = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
MESSAGE_ONLY_FORMAT = logging.Formatter('%(message)s')


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

    levels = {'debug': logging.DEBUG, 'info': logging.INFO,
              'warning': logging.WARNING, 'error': logging.ERROR,
              'critical': logging.CRITICAL}

    try:
        log_level = levels[log_level.lower()]
        echo_level = levels[echo_level.lower()]
    except KeyError:
        sys.exit('{0} is not a recognized logging level')
    else:
        log = logging.getLogger('openaccess_epub')
        log.setLevel(log_level)
        frmt = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        if log_to:
            fh = logging.FileHandler(filename=log_to)
            fh.setFormatter(frmt)
            log.addHandler(fh)
        #Add on the console StreamHandler if we are echoing to console
        if log_echo:
            sh_echo = logging.StreamHandler(sys.stdout)
            sh_echo.setLevel(echo_level)
            sh_echo.setFormatter(frmt)
            log.addHandler(sh_echo)