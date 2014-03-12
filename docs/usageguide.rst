Usage Guide
===========

Installing OpenAccess_EPUB will add the ``openaccess_epub`` module to your python libraries (see :doc:`installation` for installation
instructions), along with a command-line user interface to access some built-in utilities for EPUB production. This Guide will focus on how to
use the command interface; if you are a developer wishing to primarily make use of the ``openaccess_epub`` module or sub-modules, you may
wish to skip directly to the :doc:`moduledocs`


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
your use of OpenAccess_EPUB

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

At any point, you may re-run the `configure` command to change your settings or edit the `config.py` file. The ``oaepub clearcache manual``
command will print out the location of the cache itself as well as *attempt* to launch a platform-appropriate file browser at that location.

Interactive Configuration
+++++++++++++++++++++++++

The command `oaepub configure` will launch an interactive script for setting you configuration. Each setting has a default value contained in
square brackets "[]", if you do not wish to change the default setting you may simply press "Enter" to accept the default and move on. Each
setting should provide plenty of explanation, but it is worthwhile to re-iterate some general concepts here.

Some variable settings require
path values that may be either absolute paths or relative paths; absolute paths will be treated the same in any context by OpenAccess_EPUB
while relative paths will be treated as relative to a given input file. If you are on Windows, it should be okay for you to use "\\" or 
the UNIX "/" in your paths without issues.

For settings that allow multiple values, make sure that each individual value is separated by a comma ",".

The wildcard expansion using the "*" character in some options will expand using the name of the input file. For "journal_article.xml" that
name will be "journal_article". [#f1]_






.. rubric:: Footnotes

.. [#f1] The use of the star "*" is allowed in other contexts as well, such as ``oaepub convert --images``, but since it is a special character
   in most shells, you may need to use the following syntax at the command line ``oaepub convert --images="spam-*" foo.xml``


