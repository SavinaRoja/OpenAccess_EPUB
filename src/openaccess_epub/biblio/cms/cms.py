"""
The Chicago Manual of Style specifies the textual formatting style of
bibliographic citations. This module works with xml.dom to parse the xml
metadata of a bibliographic reference into a correctly formatted string.

This implementation may require more refinement. It should endeavor to work
with diverse input formats. An interchange specification may be needed at some
point, but that is uncertain. Alternatively, each format serving citation info
might require a pre-processing method to guide the styling of the citation.
"""

import OpenAccess_EPUB.utils as utils
import OpenAccess_EPUB.jpts as jpts
import xml.dom.minidom
import logging

log = logging.getLogger('biblio.cms')


class Citation(object):
    """
    This class is the base class for a citation in the Chicago Manual of Style.
    It must receive an appropriate xml.dom Node. Can produce text-only output
    or text with xml emphasis elements.
    """

    def __init__(self, citation_node, citation_type, text_only=False):
        """
        The initiation process.
        """
        impl = xml.dom.minidom.getDOMImplementation()
        self.doc = impl.createDocument(None, 'package', None)
        self.node = citation_node
        self.type = self.node.getAttribute('citation_type')
        self.text_only = text_only
        self.citation = None
        {'book': self.bookCitation(),
         'commun': self.communCitation(),
         'journal': self.journalCitation(),
         'newspaper': self.newspaperCitation(),
         'magazine': self.magazineCitation(),
         'review': self.reviewCitation(),
         'unpublishedManuscript': self.unpublishedManuscriptCitation(),
         'lecture': self.lectureCitation(),
         'poster': self.posterCitation(),
         'working': self.workingPaperCitation(),
         'preprint': self.preprintCitation(),
         'private': self.privateContractCitation()}[self.type]

    def bookCitation(self):
        """
        Sets self.citation per CMS guidelines for books.
        """
        pass

    def communCitation(self):
        """
        Sets self.citation per CMS guidelines for interviews and personal
        communications.
        """
        pass

    def journalCitation(self):
        """
        Sets self.citation per CMS guidelines for journals.
        """
        pass

    def newspaperCitation(self):
        """
        Sets self.citation per CMS guidelines for newspapers.
        """
        pass

    def magazineCitation(self):
        """
        Sets self.citation per CMS guideliens for magazines.
        """

    def reviewCitation(self):
        """
        Sets self.citation per CMS guidelines for reviews.
        """

    def thesisCitation(self):
        """
        Sets self.citation per CMS guidelines for theses and dissertations.
        """
        pass

    def unpublishedManuscriptCitation(self):
        """
        Sets self.citation per CMS guidelines for unpublished manuscripts.
        """
        pass

    def lectureCitation(self):
        """
        Sets self.citation per CMS guidelines for lectures, papers presented at
        meetings, and the like.
        """
        pass

    def posterCitation(self):
        """
        Sets self.citation per CMS guidelines for papers presented at poster
        sessions.
        """
        pass

    def workingPaperCitation(self):
        """
        Sets self.citation per CMS guidelines for working papers and other
        unpublished works.
        """
        pass

    def preprintCitation(self):
        """
        Sets self.citation per CMS guidelines for preprints.
        """
        pass

    def patentCitation(self):
        """
        Sets self.citation per CMS guidelines for patents.
        """
        pass

    def privateContractCitation(self):
        """
        Sets self.citation per CMS guidelines for private contracts, wills, and
        such.
        """
        pass

    def render(self):
        if self.text_only:
            return utils.serializeText(self.citation, stringlist=[])
        else:
            return self.citation
