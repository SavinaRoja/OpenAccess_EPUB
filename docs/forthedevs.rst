Developer Reference
===================

If you a developer seeking to implement support for your journal of choice, or
hoping to make some contribution to the core project of OpenAccess_EPUB, then
this section is for you! Here is where I hope to make familiarizing yourself
with the project and its code easier.

The Basic Idea
--------------

OpenAccess_EPUB converts Journal Publishing Tag Set-conforming XML into an
ePub-conforming ebook. ePub is itself a collection of XML formats that gets
wrapped up into an ordered package (then zipped and named .epub) so the work
is already half done, right? The short answer is "yes... but"; it takes a bit
of knowledge and work but that's why I wrote OpenAccess_EPUB, to make the job
of development easier. Below I'll outline the relevant specifications for ePub
as well as how to jump into the code to begin extending it.

Every ePub file must follow the Open Container Format, OCF, which you can read
about here (Links to a .doc file):`http://idpf.org/epub/20/spec/OCF_2.0.1_draft.doc <http://idpf.org/epub/20/spec/OCF_2.0.1_draft.doc>`
This contains information about file and directory placement and conventions
regarding naming and such. OpenAccess_EPUB handles the basics, but if you wish
to work on something more advanced, 

Every ePub file must follow the Open Packaging Format, OPF, which you can read
about here: `http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.4 <http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.4>`
This specifies the crucial OPF Package Document (.opf file) and Global
Declarative Navigation File (or "Navigation Center eXtended" .ncx). Together
these documents facilitate indexing and navigation of the ePub. Adding support
for a new publisher will involve extending the openaccess_epub.opf module to
ensure that these files are correctly generated from the input XML.

Finally, there is the Open Publication Structure, OPS, whose specification is
available here: `http://www.idpf.org/epub/20/spec/OPS_2.0.1_draft.htm <http://www.idpf.org/epub/20/spec/OPS_2.0.1_draft.htm>`
This defines what will serve as valid XML for the reading content of the ePub.
Despite being written for the JPTS in multiple versions, OpenAccess_EPUB is
not able to anticipate the needs of specific publishers (or not for now) due to
the variety permitted by the schema and publisher convention; this will
probably consume the majority of the time spent implementing support for a new
publisher. Fortunately, you are not alone (I am happy to help) and the work
that I have done for PLoS should serve as a good model.

Important Python Libraries
--------------------------

This project makes extensive use of the xml.dom.minidom module of the Python
Standard Library. One should read/skim the docs for that module, as well as
note that I have added some extended functions to some of its classes; you will
find these changes near the top of article.py.

