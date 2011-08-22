"""References/citations"""
from utils import getTagData
class Reference:
    """Represents bibliographical references.
    In practical terms, this means a journal citation type.
    More types may be added as necessary to support alternative citation types.
    """
    def __init__(self, referencenode, identifier):
        self.id = identifier

    def __str__(self):
        return self.id

class Journal(Reference):
    """Represents a Journal type reference."""
    def __init__(self, refnode, identifier):
        Reference.__init__(self, refnode, identifier)
        self.id = identifier
        self.authors = []
        self.label = getTagData(refnode.getElementsByTagName('label'))
        citation = refnode.getElementsByTagName('citation')[0]
        persongroup = citation.getElementsByTagName('person-group')[0]
        self.etal = False
        if len(persongroup.getElementsByTagName('etal')):
            self.etal = True
        names = persongroup.getElementsByTagName('name')
        for entry in names:
            surname = getTagData(entry.getElementsByTagName('surname'))
            givenname = getTagData(entry.getElementsByTagName('given-names'))
            self.authors.append(u'{0} {1}'.format(surname, givenname))
        self.year = getTagData(citation.getElementsByTagName('year'))
        self.title = getTagData(citation.getElementsByTagName('article-title'))
        self.source = getTagData(citation.getElementsByTagName('source'))
        self.volume = getTagData(citation.getElementsByTagName('volume'))
        self.fpage = getTagData(citation.getElementsByTagName('fpage'))
        self.lpage = getTagData(citation.getElementsByTagName('lpage'))
        
    def __str__(self):
        namestr = u''
        for name in self.authors:
            namestr = namestr + name + u', '
        if self.etal:
            namestr = namestr + u'et al. '

        formatstr = u'{0}. {1}({2}) {3} {4} {5}: {6}-{7}.'
        retstr = formatstr.format(self.label, namestr, self.year, self.title,
                                  self.source, self.volume, self.fpage,
                                  self.lpage)
        return retstr