OpenAccess_EPUB is a program for converting OpenAccess Academic Journal
articles into the ePub format.

OpenAccess_EPUB's development is focusing primarily on PLoS at the moment, but
is being designed with extensibility for additional publishers in mind.

Documentation for the project can be found at
[Read the Docs](https://openaccess_epub.readthedocs.org/en/latest/)

Getting Started
---------------
To get started with OpenAccess_EPUB, one should download the source code and
then navigate to the top-level directory in the source code. Then install the
program with Python3 (the program's officially supported Python version). The
command shown below may or may not work verbatim, replace "python3" with the
appropriate link to the Python3 executable.

For Linux users:

`sudo python3 setup.py install`

For Mac and Windows, enter:

`python3 setup.py install`

Windows systems may require additional configuration (see the wiki).

The next step is to execute OpenAccess_EPUB's configuration script. This will
allow one to define some helpful default behavior.

`oae-quickstart`

Using the configuration script with the "-d" flag will automatically generate
the system configuration file with all default values. It should inform you of
where the config file is located for inspection.

Now you are prepared to use OpenAccess_EPUB's main script "oaepub". The
following command would instruct OpenAccess_EPUB to convert the article.xml
file into an ePub file.

`oaepub -i my/article.xml`

Many more options are available as command line flags, and you can learn more
about them by executing:

`oaepub --help`

How to Contribute
-----------------
If you would like to contribute to the project, there are many ways to do so. 
If you know Python and would like to assist in development, contact me and we 
can discuss how you may help. Feedback regarding bugs, presentation, formatting,
and accessibility are all quite valuable.

Author
------
Paul Barton (SavinaRoja)
