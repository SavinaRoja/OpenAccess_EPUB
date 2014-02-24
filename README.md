OpenAccess_EPUB is a program for converting OpenAccess Academic Journal
articles into the ePub format.

OpenAccess_EPUB's development is focusing primarily on PLoS at the moment, but
is being designed with extensibility for additional publishers in mind.

Getting Started
---------------
You can install OpenAccess_EPUB from the source at the
[project page](https://github.com/SavinaRoja/OpenAccess_EPUB).

or you can install with pip.

`pip install openaccess_epub`

OpenAccess_EPUB is only compatible with Python3, so make sure that you install
it with the correct version if you have more than one Python version.

Additional requirements are [docopt](https://github.com/docopt/docopt) and
[lxml](http://lxml.de/), which pip will attempt to install for you.

Once you've successfully installed OpenAccess_EPUB and its dependencies,
access the interface using

`oaepub`

This can be followed by various subcommands and help
regarding the usage can be retrieved by

`oaepub -h`

`oaepub convert -h`
 
 etc.

Use the `oaepub configure` command to set up some local OpenAccess_EPUB
configuration interactiely before converting articles to EPUB. 

How to Contribute
-----------------
If you would like to contribute to the project, there are many ways to do so. 
If you know Python and would like to assist in development, contact me and we 
can discuss how you may help. Feedback regarding bugs, presentation, formatting,
and accessibility are all quite valuable.

Author
------
Paul Barton (SavinaRoja)
