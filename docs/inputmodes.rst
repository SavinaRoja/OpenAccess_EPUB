Input Modes
===========

OpenAccess_EPUB supports a few distinct modes of operation, called Input Modes,
which may be used to produce ePub content. Each of these modes will be
described in brief below, and will provide a link to a page with further
details.

Single Input Mode
-----------------

Single Input Mode will create a single ePub from a single article XML file. It
will work with a local XML file, or it can try to find the XML file based on
a DOI or URL. In the case of DOI, make sure that your input argument begins
with "doi:".

Batch Input Mode
----------------

Batch Input mode is essentially the same as Single Input Mode, but in series.
It is there for when you have a directory containing many XML files that you
wish to convert.

Parallel Batch Input Mode
-------------------------

Parallel Batch Input Mode may replace Batch Input mode in the future, if I can
get it working. It's the same as Batch Input Mode, and right now doesn't work
properly all the time.

Collection Input Mode
---------------------

Collection Input Mode is useful for creating a composite ePub file from
multiple article XML files. Collection Input Mode must be executed in a
directory containing all of the XML files, and the optional "order.txt" file
may be placed in the directory to specify the order of article incorporation.
There are two options for image files, either the images may be pulled from
cache or they should be in a subdirectory named "images-your_article". For
example, if the article is named "journal.pbio.0000022.xml" then the images for
that article should be in "images-journal.pbio.0000022". If both of these
options fail, then OpenAccess_EPUB may ask if it should attempt to download
them from the publisher's website.