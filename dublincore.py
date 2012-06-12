"""
This module provides a series of tools to aid in the creation of Dublin Core
metadata elements which are incorporated in the OPF specification. Relevant
specifications are: http://dublincore.org/documents/2004/12/20/dces/ and
http://idpf.org/epub/20/spec/OPF_2.0.1_draft.htm

It is important to note that only text, numbers, and special characters are
allowed inside these elements.
"""


def identifier(input_string, dom, primary=False):
    """
    This creates a dc:identifier element containing the passed string.
    """
    dc_ele = dom.createElement('dc:identifier')
    dc_txt = dom.createTextNode(input_string)
    if primary:
        dc_ele.setAttribute('id', 'PrimaryID')
    dc_ele.appendChild(dc_txt)
    return dc_ele


def language(dom, input_string='en'):
    """
    This creates a dc:language element containing the passed string. It
    defaults to english.
    """
    dc_ele = dom.createElement('dc:language')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    return dc_ele


def title(input_string, dom):
    """
    This creates a dc:title element containing the passed string.
    """
    dc_ele = dom.createElement('dc:title')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    return dc_ele


def rights(input_string, dom):
    """
    This creates a dc:rights element containing the passed string.
    """
    dc_ele = dom.createElement('dc:rights')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    return dc_ele


def creator(input_string, file_as, dom):
    """
    This creates a dc:creator element containing the passed string. It is
    extended by the OPF specification to add opf:role and opf:file-as
    """
    dc_ele = dom.createElement('dc:creator')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    dc_ele.setAttribute('opf:role', 'aut')
    dc_ele.setAttribute('opf:file-as', file_as)
    return dc_ele


def contributor(input_string, dom, file_as=False, role='edt'):
    """
    This creates a dc:contributor element containing the passed string. It is
    extended by the OPF specification to add opf:role and opf:file-as
    (the latter being optional)
    """
    dc_ele = dom.createElement('dc:contributor')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    dc_ele.setAttribute('opf:role', role)
    if file_as:
        dc_ele.setAttribute('opf:file-as', file_as)
    return dc_ele


def coverage(input_string, dom):
    """
    This creates a dc:coverage element containing the passed string. It is not
    yet used.
    """
    dc_ele = dom.createElement('dc:coverage')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    return dc_ele


def date(year, month, day, event, dom):
    """
    This creates a dc:date element containing the passed string. It is extended
    by the OPF specification to add opf:event to specify distinct dates such as
    creation, publication, modification and others (the values are not strictly
    defined). Note that the string should be formatted according to
    http://www.w3.org/TR/NOTE-datetime
    """
    imonth, iday = int(month), int(day)
    d_string = year
    if imonth:
        d_string += '-{0}'.format(month)
        if iday:
            d_string += '-{0}'.format(day)
    dc_ele = dom.createElement('dc:date')
    dc_txt = dom.createTextNode(d_string)
    dc_ele.appendChild(dc_txt)
    dc_ele.setAttribute('opf:event', event)
    return dc_ele


def source(input_string, dom):
    """
    This creates a dc:source element containing the passed string. It is not
    yet used.
    """
    dc_ele = dom.createElement('dc:source')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    return dc_ele


def epubformat(dom):
    """
    This creates a dc:format element whose value will be
    \'application/epub+zip\'
    """
    dc_ele = dom.createElement('dc:format')
    dc_txt = dom.createTextNode('application/epub+zip')
    dc_ele.appendChild(dc_txt)
    return dc_ele

