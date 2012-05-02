"""
This module will provide useful classes and functions for representing
article contributions as defined in the Journal Publishing Tag Set.
"""

import collections


class ContribGroup(object):
    """
    <contrib-group> is an optional, zero or more, element used to group
    elements used to represent individuals who contributed independently
    to the article. It is not to be confused with <collab>. Beneath this
    element, it may contain <contrib> elements for individual authors or
    editors. It may also contain many of the elements contained within
    <contrib> elements. Should these elements exist, they are presumably
    pertinent to all <contrib> members contained, and will be applied to
    those elements unless overridden during their inspection.
    
    Description
        The following, in order:
            Contributor <contrib>, one or more
            Any combination of:
            Address/Contact Information <address>
            Affiliation <aff>
            Author Comment <author-comment>
            Biography <bio>
            All the address linking elements:
                Email Address <email>
                External Link <ext-link>
                Uniform Resource Indicator (URI) <uri>
            On Behalf of <on-behalf-of>
            Role or Function Title of Contributor <role>
            X(cross) Reference <xref>
    """
    def __init__(self, contrib_group_node):
        self.Node = contrib_group_node
        self.content_type = self.Node.getAttribute('content-type')
        self.id = self.Node.getAttribute('id')
        self.contrib = self.getContrib()
        self.address = self.getAddress()  # NodeList
        self.aff = self.getAff()  # List of named(Node, id, rid, content_type)
        self.author_comment = self.getAuthorComment()  # NodeList
        self.bio = self.getBio()
        self.email = self.getEmail()
        self.ext_link = self.getExtLink()
        self.uri = self.getUri()
        self.on_behalf_of = self.getOnBehalfOf()
        self.role = self.getRole()
        self.xref = self.getXref()
    
    def getChildrenByTagName(self, searchterm):
        """
        Many of the elements that may exist under <contrib-node> can also
        be found under <contrib>. Only those that are direct descendants of a
        node should be considered, so this method is to be used in place of
        getElementsByTagName() which looks beyond immediate children.
        """
        nodelist = []
        for c in self.Node.childNodes:
            try:
                tag = c.tagName
            except AttributeError:  # Text nodes have no tagName
                pass
            else:
                if tag == searchterm:
                    nodelist.append(c)
        return nodelist
    
    def getContrib(self):
        return self.Node.getElementsByTagName('contrib')
        
    def getAddress(self):
        """
        The <address> element under <contrib-group> and <contrib> elements has
        the following attributes (by DTD version).
        2.0 : id
        2.3 : id, content-type
        3.0 : id, content-type, specific-use
        It may contain any of the address elements and/or the address linking
        elements. This method returns a list of address elements directly
        below the parent node.
        """
        return self.getChildrenByTagName('address')
        
    def getAff(self):
        """
        The <aff> element under <contrib-group> and <contrib> elements has the
        following attributes (by DTD version).
        2.0 : id, rid
        2.3, 3.0 : content-type, id, rid
        It has diverse content specifications and implementation is likely to
        vary widely between publishers.
        """
        affs = self.getChildrenByTagName('aff')
        at = collections.namedtuple('Aff', 'Node, id, rid, content_type')
        afflist = []
        for aff in affs:
            aid = aff.getAttribute('id')
            rid = aff.getAttribute('rid')
            ct = aff.getAttribute('content-type')
            afflist.append(at(aff, aid, rid, ct))
        return afflist
    
    def getAuthorComment(self):
        """
        <author-comment> is an optional tag, 0 or more, that may contain a
        <title> element and 1 or more <p> elements. 
        """
        return self.getChildrenByTagName('author-comment')
    
    def getBio(self):
        """
        <bio> is an optional tag, 0 or more, that may contain a <title>
        element and 1 or more <p> elements.
        """
        return self.getChildrenByTagName('bio')
    
    def getEmail(self):
        """
        
        """
        return self.getChildrenByTagName('email')
    
    def getExtLink(self):
        """
        
        """
        return self.getChildrenByTagName('ext-link')
    
    def getUri(self):
        """
        
        """
        return self.getChildrenByTagName('uri')
    
    def getOnBehalfOf(self):
        """
        
        """
        return self.getChildrenByTagName('on-behalf-of')
    
    def getRole(self):
        """
        
        """
        return self.getChildrenByTagName('role')
    
    def getXref(self):
        """
        
        """
        return self.getChildrenByTagName('xref')
    
    def contributors(self):
        """
        This method instantiates a Contrib class for each <contrib> element
        contained in the <contrib-group> element. These instances are returned
        inside a list.
        """
        contriblist = []
        for tag in self.contrib:
            contriblist.append(Contrib(tag))
        return contriblist
    
class Contrib(ContribGroup):
    """
    <contrib> nodes are similar in specification to <contrib-group> nodes,
    thus they inherit from the ContribGroup class. Aside from collecting
    some different data during inspection, this class is set up to accept
    default values for attributes it might inherit from its parent
    <contrib-group> node.
    """
    
    
    
    def getContrib(self):
        """
        <contrib> nodes do not contain further <contrib> nodes
        """
        return None