"""Crossreferences"""

class Xref:
    """The top level class of crossreferences."""
    def __init__(self, xrefnode):
        self.rid = xrefnode.getAttribute('id')
        
    def __str__(self):
        return 'Reference ID: {0}'.format(self.rid)


class Affiliation(Xref):
    """An affiliation crossreference."""
    def __init__(self, xrefnode):
        Xref.__init__(self, xrefnode)
        self.address = None
        addrline = xrefnode.getElementsByTagName('addr-line')
        if addrline:
            self.address = addrline[0].firstChild.data
        
    def __str__(self):
        return 'Reference ID: {0}, Address Line: {1}'.format(self.rid,
                                                             self.address)
        
class Correspondence(Xref):
    """A Correspondence crossreference."""
    def __init__(self, xrefnode):
        Xref.__init__(self, xrefnode)
        self.address = None
        addrline = xrefnode.getElementsByTagName('addr-line')
        if addrline:
            self.address = addrline[0].firstChild.data
        self.email = None
        email = xrefnode.getElementsByTagName('email')
        if email:
            self.email = email[0].firstChild.data
        
    def __str__(self):
        out = 'Reference ID: {0}, Address Line: {1}, Email: {2}'
        return out.format(self.rid, self.address, self.email)
