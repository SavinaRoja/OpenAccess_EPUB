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
    Configures logging to do nothing
    """
    log = logging.getLogger('openaccess_epub')
    log.addHandler(logging.NullHandler())


def config_logging(log_to, log_level, log_echo, echo_level):
    """
    Configures and generates a Logger object based on common parameters used for
    console script execution in OpenAccess_EPUB.

    These parameters are:
      log_to - Defines a log file location, if False, filename will not be set
      log_level - Defines the logging level
      log_echo - If True, log data will also print to console
      echo_level - Defines the logging level of console-printed data

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