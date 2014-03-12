Installation
============

OpenAccess_EPUB is not developed for compatibility with Python2, so you should first make sure that you are working with a version of
Python3. http://www.python.org/download/releases/

OpenAccess_EPUB should work equally well on Linux, Mac, or Windows, but installation procedures may differ between platforms. 

The program can be installed from source via

    python setup.py install

or (preferably, because it will also install dependencies) by pip with

    pip install openaccess_epub

Dependencies
------------

* `docopt <https://github.com/docopt/docopt>`_ is required to utilize OpenAccess_EPUB's command-line user interface. Those who don't care to
  utilize the interface may forego this dependency.

* `lxml <http://lxml.de>`_ provides the core XML parsing and manipulation library for OpenAccess_EPUB. Compiling/installing lxml on Linux will
generally require the libxml2 and libxslt packages being installed. If you are having trouble installing lxml on Windows, perhaps try the
`appropriate unofficial pre-compiled binary <http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml>`_

After installation, if you wish to use the OpenAccess_EPUB interface and utilities for producing EPUB, make sure you configure the software
prior to use, see :ref:`configuration`.
