"""contributor.py"""
from utils import getTagData

class Contributor:
    """Represents a contributor to the article.
    In practical terms, this generally means either an Author,
    or an Editor when it comes to academic journalism.
    More may be added as necessary to this class.
    """
    def __init__(self, contribnode):
        self.surname = ''
        self.givenname = ''
        self.affiliation = []
        self.contact = []
        
        namenode = contribnode.getElementsByTagName('name')[0]
        self.givenname = getTagData(namenode.getElementsByTagName('given-names'))
        self.surname = getTagData(namenode.getElementsByTagName('surname'))
        
        self.xrefs = contribnode.getElementsByTagName('xref')

        for ref in self.xrefs:
            reftype = ref.getAttribute('ref-type')
            if reftype == 'aff':
                self.affiliation.append(ref.getAttribute('rid'))
            elif reftype == 'corresp':
                self.contact.append(ref.getAttribute('rid'))

    def __str__(self):
        out = 'Surname: {0}, Given Name: {1}, AffiliationID: {2}, Contact: {3}'
        return out.format(self.surname, self.givenname,
                          self.affiliation, self.contact)

    def get_name(self):
        """Get the name. Formatted as: Carl Sagan"""
        return('{0} {1}'.format(self.givenname, self.surname))

class Author(Contributor):
    """Represents an author."""
    def __init__(self, contribnode):
        Contributor.__init__(self, contribnode)

class Editor(Contributor):
    """Represents an editor."""
    def __init__(self, contribnode):
        Contributor.__init__(self, contribnode)
