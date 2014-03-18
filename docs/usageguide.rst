Usage Guide
===========

Installing OpenAccess_EPUB will add the ``openaccess_epub`` module to your python libraries (see :doc:`installation` for installation
instructions), along with a command-line user interface to access some built-in utilities for EPUB production. This Guide will focus on how to
use the command interface; if you are a developer wishing to primarily make use of the ``openaccess_epub`` module or sub-modules, you may
wish to skip directly to the :doc:`modules`


`oaepub` Interface
------------------

The `oaepub` command should be available once you have installed OpenAccess_EPUB. `oaepub` will be the command prefix for every action
executed by OpenAccess_EPUB. `oaepub` provides access to several sub-commands for different jobs. If you have ever used `git`, then you are
familiar with this kind of interface with sub-commands (`git add`, `git commit`, etc.)

Using the ``-h`` or ``--help`` option  will always tell you how to use the command or sub-command. Try the following:

  ``oaepub --help``

It should print the following to your console:

.. I haven't figured out a better way of doing this yet

.. literalinclude:: ../scripts/oaepub
     :lines: 5-27

You should observe the command `configure` among the list of available commands, which will allow you to define configuration variables for
your use of OpenAccess_EPUB.

.. _configuration:

Configuration
-------------

Before the majority of OpenAccess_EPUB commands will work, you must set up some configuration options. Configuration may be done by
interactive prompt using the command

  ``oaepub configure``

Or the configuration may be set to normal defaults using

  ``oaepub configure --default``

The information for your configuration will be stored in a Python file called `config.py`. It will be located in the base directory of your
OpenAccess_EPUB cache, to find out where this is, use the command

  ``oaepub configure where``

At any point, you may re-run the `configure` command to change your settings or edit the `config.py` file in a text editor. The
``oaepub clearcache manual`` command will print out the location of the cache itself as well as *attempt* to launch a platform-appropriate
file browser at that location.

Interactive Configuration
+++++++++++++++++++++++++

The command `oaepub configure` will launch an interactive script for setting you configuration. Each setting has a default value contained in
square brackets "[]", if you do not wish to change the default setting you may simply press "Enter" to accept the default and move on. Each
setting should provide plenty of explanation, but it is worthwhile to re-iterate some general concepts here.

Some variable settings require
path values that may be either absolute paths or relative paths; absolute paths will be treated the same in any context by OpenAccess_EPUB
while relative paths will be treated as relative to a given input file. If you are on Windows, it should be okay for you to use "\\" or 
the unix-style "/" in your paths without issues.

For settings that allow multiple values, make sure that each individual value is separated by a comma ",".

The wildcard expansion using the "*" character in some options will expand using the name of the input file. For "journal_article.xml" that
name will be "journal_article". [#f1]_

.. conversion-overview

Overview of Conversion Commands with Examples
---------------------------------------------

There are three commands for the purpose of converting OpenAccess journal articles to EPUB documents: `convert`, `batch`, and `collection`.

* The `convert` command is a general tool for converting one to a few journal article input files into individual EPUB files.

* The `batch` command is specialized for converting large quantities of journal article input files (contained within a directory) into EPUB
  individual files.

* The `collection` command is specialized to take advantage of a powerful feature of OpenAccess_EPUB; it can convert several journal article
  input files into a single EPUB file representing a collection or omnibus.

Speaking of input files...

Input, what Input?
++++++++++++++++++

OpenAccess_EPUB always operates on a special XML (.xml extension) file produced by the journal publisher that contains all of the data and
metadata for the article. These .xml files are constructed according to various versions of a standard called the
`Journal Publishing Tag Set <http://dtd.nlm.nih.gov/publishing/>`_ . That said, the `convert` command will also work with the appropriate DOI
or URL for a journal article if online-fetching support has been provided for the specific publisher. In this case, it will download the XML
file automatically. If this fails, you will need to download the file manually.

`convert`
+++++++++

Let's suppose that we wish to convert the PLoS Computational Biology article located at this URL
http://www.ploscompbiol.org/article/info%3Adoi%2F10.1371%2Fjournal.pcbi.1003450 to an EPUB file. We have the following three options for
specifying this article to the `convert command`:

  ``oaepub convert "http://www.ploscompbiol.org/article/fetchObjectAttachment.action?uri=info%3Adoi%2F10.1371%2Fjournal.pcbi.1003450&representation=XML"``

  ``oaepub convert doi:10.1371/journal.pcbi.1003450``

  ``oaepub convert path/to/journal.pcbi.1003450.xml``

For the first option we copied and pasted the link to the XML file from the sidebar, and enclosed it in quotes to avoid issues with
special characters. For the second option we simply find the DOI listed for the article on the web page. For the third option we download 
the XML file from the web page's sidebar to our hard drive, then provide the path to the file as the input argument. In the first two 
options, the command would download the XML file to the working directory in which the command was executed as the first step. We'll
procede from the third example.

Assuming default configuration, the output EPUB file would be located in the same directory as the input XML file as
``path/to/journal.pcbi.1003450.epub``. If we wanted to place the output somewhere else, we could use the ``--output`` (``-o``) option like:

  ``oaepub convert -o my/articles/folder path/to/journal.pcbi.1003450.xml``

If we wanted to have no information printed out during conversion, we could use ``--silence`` (``-s``) like:

  ``oaepub convert -s path/to/journal.pcbi.1003450.xml``

Or we could have more information printed out using ``--verbosity`` (``-V``) like:

  ``oaepub convert --verbosity DEBUG path/to/journal.pcbi.1003450.xml``

For more information and options with the `convert` command refer to ``oaepub convert --help``

`batch`
+++++++

The `batch` command's job is to convert all articles in a directory (or multiple directories) to EPUB. This is somewhat like running 
`convert` on each article (``oaepub convert ./*.xml`` *would work* ), but provides a few useful additional features for large batch jobs.
It will not stop to ask about file or directory name conflicts, it will simply skip converting the article at issue.
A simple example might be:

  ``oaepub batch articles_dir/``

where "articles" is a directory which contains XML files for journal articles. This example would create a log file for each article it
processed to EPUB, what if we wanted to only log all errors into a single file for the whole batch? We might use the ``--log-to``
(``-l``) and ``--log-level`` options like this:

  ``oaepub batch --log-to batch_errors.log --log-level ERROR articles_dir/``

OpenAccess_EPUB can locate the images for an article on your local machine either from the cache or relative to the input (this behavior
is configurable see :ref:`configuration`). If we want to explicitly specify a pattern for finding images for an article based on "*"
name matching, we could use the ``--images`` (``-i``) option like this for input-relative images:

  ``oaepub batch --images ./images/*  articles_dir/``

which would find image directories of with the path "articles_dir/images/{input-file-name}".

The ``--recursive`` (``-r``) option will instruct the `batch` command to recursively traverse sub-directories of each listed directory
input to convert their contained XML files as well.

For more information and options with the `batch` command refer to ``oaepub batch --help``


`collection`
++++++++++++

The `collection` command is similar to the `batch` command, however it expects a text file as its input. The name of the text file will
become the name of the EPUB, as well as the name of the single log file (unless ``--log-to`` is employed). Each line of the file should
contain a path to a local XML file; the order of the files listed will be the order of the articles in the EPUB document. An example
collection text file could read like this (all lines are valid)::

   ./first_article.xml
   ../second_article.xml
   nested/directory/third_article.xml
   /absolute/path/to/fourth_article.xml

If this file is named Reading_List_2014.txt, then the following command could be used to create the collection EPUB.

  ``oaepub collection Reading_List_2014.txt``

For more information and options with the `collection` command refer to ``oaepub collection --help``


.. rubric:: Footnotes

.. [#f1] The use of the star "*" for wildcard-expansion is usable in the config.py file and in certain command-line options (such as 
   ``oaepub batch --images``). In many shells "*" is a special character so you may need to use the following syntax to avoid its
   special treatment: ``oaepub batch --images="spam-*" articles_dir/``

