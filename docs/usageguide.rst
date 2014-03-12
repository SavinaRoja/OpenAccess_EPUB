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
     :lines: 5-29

.. _configuration:

Configuration
-------------

An important first step after installing OpenAccess_EPUB is to run the configuration command

Run `oaepub configure`
