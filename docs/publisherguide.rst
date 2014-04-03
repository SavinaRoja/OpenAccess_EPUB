Guide to adding publisher support
=================================

It's non-trivial, but believe it or not, the majority of the work has already
been laid down in terms or framework.  Despite the use of common XML publishing
formats, publishers still have a very wide array of options in terms how they
store metadata in their source document, in addition to the discretion that
publishers may wish to exercise in the construction of content from the source
XML. Due to this, publisher-specific code for the conversion of articles to
EPUB is a necessary evil (or good, depending on how you look at it); there is
no true silver-bullet solution for everyone. OpenAccess_EPUB has been designed
as a modular framework into which one may easily "plugin" code to support a new
publisher (for either/both of EPUB2 and EPUB3). This guide will walk you
through the process of extending publisher support using my work on PLoS as
a reference implementation.

Where to put the file for publisher support?
--------------------------------------------
First ask yourself, "Do I want to modify the source code of my installation
of OpenAccess_EPUB?" If you are working in a
(virtualenv)[http://www.virtualenv.org/en/latest/] or planning on committing
changes to the standard distribution of OpenAccess_EPUB, then the answer may
be "yes" (see option 2). Otherwise you may want to take advantage of putting
your code in the **publisher_plugins** sub-directory of the OpenAccess_EPUB
cache (see option 1).

1. If a folder named "publisher_plugins" does not exist in your
   OpenAccess_EPUB cache (`oaepub clearcache manual` should tell you where it
   is), create one. In that folder create your code file 
   "<short-publisher-name>.py". In that folder there should be a file called
   **doi_map**. This file may have any number of lines; each line should begin
   with a publisher DOI (for example, 10.1371 is PLoS'), followed by a ":", and
   end with the same "<short-publisher-name>" used for the code file.
   `10.1371: plos` would be a valid line-entry for a code file named "plos.py".

2. In the module folder for `openaccess_epub.publisher`, create a code file
   named "<short-publisher-name>.py". In the "__init__.py" file for the module
   you should create an entry in the `doi_map` dictionary so that
   `doi_map[<publisher-doi>]` will result in "<short-publisher-name>". The
   following mapping would be valid for PLoS, with a file named "plos.py":
   `doi_map={.., '10.1371' : 'plos', ..}`. Alternatively, you could make this
   mapping using the "doi_map" file described above in option 1.

The `openaccess_epub.publisher` module is thus equipped to treat the publisher
code in the "publisher_plugins" directory as though it were installed with the
rest of the package.

Inheriting from `openaccess_epub.publisher.Publisher`
-----------------------------------------------------


