# -*- coding: utf-8 -*-

"""
Responsible for the conversion of the Tag Suite citation elements to xhtml
content for display in an ePub.

Reference material may be found here:
https://github.com/PLOS/ambra/blob/master/base/src/main/resources/viewnlm-v2.3.xsl
"""

from lxml import etree

class CitationFormatter(object):
    """
    
    """

    def __init__(self):
        pass

def format_citation(citation, citation_type=None):
    """
    This method may be built to support elements from different Tag Suite
    versions with the following tag names:
        citation, element-citation, mixed-citation, and nlm-citation

    The citation-type attribute is optional, and may also be empty; if it has a
    value then it should appear in the following prescribed list, or it will be
    treated as 'other'.

    book          Book or book series
    commun        Informal or personal communication, such as a phone call or
                  an email message
    confproc      Conference proceedings
    discussion    Discussion among a group in some forum — public, private, or
                  electronic — which may or may not be moderated, for example,
                  a single discussion thread in a listserv
    gov           Government publication or government standard
    journal       Journal article
    list          Listserv or discussion group (as an entity, as opposed to a
                  single discussion thread which uses the value “discussion”)
    other         None of the listed types.
    patent        Patent or patent application
    thesis        Work written as part of the completion of an advanced degree
    web           Website

    This method will accept a passed citation_type argument which will override
    checking of the element's citation-type attribute and force the formatting
    according to the passed string value. Note that this may not be appropriate
    in many cases.
    """
    cite_types = {'book': self.format_book_citation,
                  'commun': self.format_commun_citation,
                  'confproc': self.format_confproc_citation,
                  'discussion': self.format_discussion_citation,
                  'gov': self.format_gov_citation,
                  'journal': self.format_journal_citation,
                  'list': self.format_list_citation,
                  'other': self.format_other_citation,
                  'patent': self.format_patent_citation,
                  'thesis': self.format_thesis_citation,
                  'web': self.format_web_citation,
                  '': self.format_other_citation,  # Empty becomes 'other'
                  None: self.format_other_citation}  # None becomes 'other'

    #Only check if no citation_type value is passed
    if citation_type is None:
        #Get the citation-type attribute value
        if 'citation-type' in nlm_citation.attrib:
            citation_type = nlm_citation.attrib['citation-type']

    #Pass the citation to the appropriate function and return result
    return cite_types[citation_type](citation)

    @staticmethod
    def format_book_citation(self, citation):
        """
        citation-type=\"book\"
        """
        #Get the count of authors
        author_group_count = int(citation.xpath('count(person-group) + count(collab)'))
        #Detect if there are non-authors
        if citation.xpath('person-group[@person-group-type!=\'author\']'):
            non_authors = True
        else:
            non_authors= False
        #Detect article-title
        if citation.xpath('article-title'):
            article_title = True
        else:
            article_title = False
        #Find out if there is at least one author or compiler
        auth_or_comp = False
        for person_group in citation.findall('person-group'):
            if 'person-group-type' in person_group.attrib:
                if person_group.attrib['person-group-type'] in ['author', 'compiler']:
                    auth_or_comp = True
                    break

        #These pieces of information allow us to provide two special use cases
        #and one general use case.
        #First special case:
        if author_group_count > 0 and non_authors and article_title:
            pass

        #Second special case
        elif auth_or_comp:
            pass

        #General case
        else:
            pass

    @staticmethod
    def format_commun_citation(self, citation):
        """
        citation-type=\"commun\"
        """

    @staticmethod
    def format_confproc_citation(self, citation):
        """
        citation-type=\"confproc\"
        """

    @staticmethod
    def format_discussion_citation(self, citation):
        """
        citation-type=\"discussion\"
        """

    @staticmethod
    def format_gov_citation(self, citation):
        """
        citation-type=\"gov\"
        """

    @staticmethod
    def format_journal_citation(self, citation):
        """
        citation-type=\"journal\"
        """

    @staticmethod
    def format_list_citation(self, citation):
        """
        citation-type=\"list\"
        """
    @staticmethod
    def format_other_citation(self, citation):
        """
        citation-type=\"other\"
        """

    @staticmethod
    def format_patent_citation(self, citation):
        """
        citation-type=\"patent\"
        """

    @staticmethod
    def format_thesis_citation(self, citation):
        """
        citation-type=\"thesis\"
        """
        #Treat the same as "book"
        return format_book_citation(citation)

    @staticmethod
    def format_web_citation(self, citation):
        """
        citation-type=\"web\"
        """


