# -*- coding: utf-8 -*-
"""
This module will provide useful classes and functions for representing
article contributions as defined in the Journal Publishing Tag Set.
"""

import collections
import openaccess_epub.utils as utils
import openaccess_epub.utils.element_methods as element_methods
import logging

log = logging.getLogger('jptscontrib')


#TODO: I've got to come through and clean some of this stuff up

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
        log.info('Parsing contrib-group node')
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
        return element_methods.get_children_by_tag_name('address', self.Node)

    def getAff(self):
        """
        The <aff> element under <contrib-group> and <contrib> elements has the
        following attributes (by DTD version).
        2.0 : id, rid
        2.3, 3.0 : content-type, id, rid
        It has diverse content specifications and implementation is likely to
        vary widely between publishers.
        """
        affs = element_methods.get_children_by_tag_name('aff', self.Node)
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
        return element_methods.get_children_by_tag_name('author-comment', self.Node)

    def getBio(self):
        """
        <bio> is an optional tag, 0 or more, that may contain a <title>
        element and 1 or more <p> elements.
        """
        return element_methods.get_children_by_tag_name('bio', self.Node)

    def getEmail(self):
        """
        <email> is an optional tag, 0 or more. It contains only text, numbers,
        and special characters.
        """
        return element_methods.get_children_by_tag_name('email', self.Node)

    def getExtLink(self):
        """
        <ext-link> is an optional tag, 0 or more. It contains text and emphasis
        elements.
        """
        return element_methods.get_children_by_tag_name('ext-link', self.Node)

    def getUri(self):
        """
        <uri> is an optional tag, 0 or more. It contains only text, numbers,
        and special characters.
        """
        return element_methods.get_children_by_tag_name('uri', self.Node)

    def getOnBehalfOf(self):
        """
        <on-behalf-of> is an optional tag, 0 or more. It contains text and
        emphasis elements.
        """
        return element_methods.get_children_by_tag_name('on-behalf-of', self.Node)

    def getRole(self):
        """
        <role> is an optional tag, 0 or more. It contains text and emphasis
        elements.
        """
        return element_methods.get_children_by_tag_name('role', self.Node)

    def getXref(self):
        """
        <xref> is an optional tag, 0 or more. It may contain text and emphasis
        elements. It's attributes are \"id\", \"rid\", and \"ref-type\". This
        method will return a list of namedtuple(node, id, rid, ref_type)
        """
        xref = collections.namedtuple('Xref', 'node, id, rid, ref_type')
        xreflist = []
        for x in element_methods.get_children_by_tag_name('xref', self.Node):
            xid = x.getAttribute('id')
            rid = x.getAttribute('rid')
            rt = x.getAttribute('ref-type')
            xreflist.append(xref(x, xid, rid, rt))
        return xreflist

    def contributors(self):
        """
        This method instantiates a Contrib class for each <contrib> element
        contained in the <contrib-group> element. These instances are returned
        inside a list.
        """
        contriblist = []
        inheritance = [self.address, self.aff, self.author_comment, self.bio,
                      self.email, self.ext_link, self.uri, self.on_behalf_of,
                      self.role, self.xref]
        for tag in self.contrib:
            contriblist.append(Contrib(tag, inheritance))
        return contriblist


class Contrib(ContribGroup):
    """
    <contrib> nodes are similar in specification to <contrib-group> nodes,
    thus they inherit from the ContribGroup class. Aside from collecting
    some different data during inspection, this class is set up to accept
    default values for attributes it might inherit from its parent
    <contrib-group> node.
    """
    def __init__(self, contribnode, inheritance):
        ContribGroup.__init__(self, contribnode)
        self.getAttributes()
        self.anonymous = self.getAnonymous()
        self.collab = self.getCollab()
        self.name = self.getName()
        self.degrees = self.getDegrees()
        #This list must directly correlate to the inheritance list
        inheritors = [self.address, self.aff, self.author_comment, self.bio,
                      self.email, self.ext_link, self.uri, self.on_behalf_of,
                      self.role, self.xref]
        i = 0
        while i < len(inheritors):
            if not inheritors[i]:
                if inheritance[i]:
                    inheritors[i] = inheritance[i]
            i += 1

    def getAttributes(self):
        self.attrs = {}
        attrs = ['contrib-type', 'corresp', 'deceased', 'equal-contrib', 'id',
                 'rid', 'xlink:actuate', 'xlink:href', 'xlink:role',
                 'xlink:show', 'xlink:title', 'xlink;type', 'xlink:xlink']
        for a in attrs:
            self.attrs[a] = self.Node.getAttribute(a)

    def getAnonymous(self):
        """
        <anonymous> is an optional element, and typically contains no content.
        Additionally, it should be rare that it should be ever more than 0 or 1
        but the JPTS does not restrict its value. For this reason, it will be
        collected as a NodeList. It does not exist in v2.0.
        """
        return element_methods.get_children_by_tag_name('anonymous', self.Node)

    def getCollab(self):
        """
        <collab> is an optional element, 0 or more, though again it should be
        a rare case that multiple <collab> tags are listed under a single
        <contrib>. This tag is used when authors work in collaboration, or a
        group entity is to be identified as the author, such as a corporation
        or academic institution.
        """
        return element_methods.get_children_by_tag_name('collab', self.Node)

    def getName(self):
        """
        <name> is an optional element, 0 or more, but should rarely be multiple
        within a single <contrib>. If multiple names are present, it shall be
        considered the case that each name applies to a singular contributing
        entity. For example, Pamela Isley might also be known as Paula Irving
        or Poison Ivy. The content model of <name> requires a single <surname>
        and 0 or one of the following: <given-name>, <prefix>, and <suffix>
        (all of which are text, numbers, special characters). The possible
        attributes are \"name-style\" and \"content-type\".
        """
        namelist = []
        name = collections.namedtuple('Name', 'Node, surname, given, prefix, suffix, name_style, content_type')
        for n in element_methods.get_children_by_tag_name('name', self.Node):
            surname = utils.nodeText(n.getElementsByTagName('surname')[0])
            try:
                given = utils.nodeText(n.getElementsByTagName('given-names')[0])
            except IndexError:
                given = None
            try:
                prefix = utils.nodeText(n.getElementsByTagName('prefix')[0])
            except IndexError:
                prefix = None
            try:
                suffix = utils.nodeText(n.getElementsByTagName('suffix')[0])
            except IndexError:
                suffix = None
            ns = n.getAttribute('name-style')
            ct = n.getAttribute('content-type')
            namelist.append(name(n, surname, given, prefix, suffix, ns, ct))
        return namelist

    def getDegrees(self):
        """
        <degrees> is an optional element, 0 or more, under the <contrib> tag.
        It may only contain text, numbers, or special characters, and is
        intended to contain credential information that may be displayed with
        the name. For multiple degrees, a publisher may hypothetically do
        either of the following: <degrees>PhD, MD</degrees> or 
        <degrees>PhD</degrees><degrees>MD</degrees>.
        """
        degreeslist = []
        for degrees in element_methods.get_children_by_tag_name('degrees', self.Node):
            degreeslist.append(utils.nodeText(degrees))

    def getContrib(self):
        """
        <contrib> nodes do not contain further <contrib> nodes
        """
        return None