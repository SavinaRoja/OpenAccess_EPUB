Installation
============

OpenAccess_EPUB is not developed for compatibility with Python2, so you should first make sure that you are working with a version of
Python3. http://www.python.org/download/releases/

OpenAccess_EPUB should work equally well on Linux, Mac, or Windows, but installation procedures may differ between platforms. 

The program can be installed from source via

    python setup.py install

or (preferably, because it will also install dependencies) by pip with

    pip install openaccess_epub

After installation, if you wish to use the OpenAccess_EPUB interface and utilities for producing EPUB, make sure you configure the software
prior to use, see :ref:`configuration`.

Dependencies
------------

* `docopt <https://github.com/docopt/docopt>`_ is required to utilize OpenAccess_EPUB's command-line user interface. Those who don't care to
  utilize the interface may forego this dependency.

* `lxml <http://lxml.de>`_ provides the core XML parsing and manipulation library for OpenAccess_EPUB. Compiling/installing lxml on Linux will
  generally require the libxml2 and libxslt packages being installed. If you are having trouble installing lxml on Windows, perhaps try the
  `appropriate unofficial pre-compiled binary <http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml>`_

Using EpubCheck
---------------

EpubCheck is an important piece of software produced by the `International Digital Publishing Forum <http://idpf.org/>`_ that
validates EPUB documents. OpenAccess_EPUB will attempt to validate all of its EPUB output using EpubCheck by default. In order for this to
be successful, you must have Java installed on your computer and the EpubCheck .jar file. You can find EpubCheck releases at 
https://github.com/IDPF/epubcheck/releases . The ``epubcheck_jarfile`` value in your config file should then be set to the absolute path to
the .jar file. This will also be covered by running ``oaepub configure`` and in the :ref:`configuration` section.

If you are using OpenAccess_EPUB as a library or for personal use, EpubCheck may not be necessary. If you intend to use OpenAccess_EPUB for
publishing EPUB, use of EpubCheck is vital for quality assurance.
