This project aims to demonstrate that, with minimal effort, PLoS journal articles can be distributed in ebook (EPUB) format by producing well-formatted EPUB books from PLoS' provided XML documents.

IDPF Specifications for epub v2.0.1
Open Publication Structure (OPS):
http://www.idpf.org/doc_library/epub/OPS_2.0.1_draft.htm
Open Packaging Format (OPF):
http://www.idpf.org/doc_library/epub/OPF_2.0.1_draft.htm
Open Container Format (OCF):
http://www.idpf.org/doc_library/epub/OCF_2.0.1_draft.doc

PLoS uses the TOPAZ Publishing Platform:
http://www.plos.org/about/faq.php#topaz

Articles use the Journal Publishing Tag Set DTD v2.0:
http://dtd.nlm.nih.gov/publishing/2.0/journalpublishing.dtd
Journal Publishing DTD Tag Library version 2.0:
http://dtd.nlm.nih.gov/publishing/tag-library/2.0/index.html

The tag library for the current tag set (v3.0) may also be useful:
http://dtd.nlm.nih.gov/publishing/tag-library/

PLoS EPUB seeks to be an entirely self-sufficient program that only requires the input of the PLoS XML files and produce an ebook file in accordance with the EPUB specifications.
Such a format could benefit the open access movement by opening a new channel for distribution that may proivde a more optimal reading environment for some readers.
In contrast to the convention of online digital publishing of scientific journalism via PDF, which stresses fidelity to the printed page, reflowable ebook formats allow readers to alter text size, width, and font for improved reading (a very notable benefit for the visually impaired) while still exercising almost as full a range of hypertextual enhancements as available to PDF (the notable distinctions being the lack of direct* video and audio support on most reading systems; this is a minute disadvantage considering the rarity of their implementation in scientific literature).

*Most reading systems, including more modern reading devices support web browsing. Links to web material is not optimal, but should still be a fairly reliable method of delivering this content should it prove necessary.

The main workflow is expected to proceed according to the following steps. Gather information from the input XML. Grab supporting files from the web. Create file indices. Create output XML files for EPUB. Compress into EPUB package.

