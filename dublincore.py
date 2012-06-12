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
    This creates a dc:rights elment containing the passed string.
    """
    dc_ele = dom.createElement('dc:rights')
    dc_txt = dom.createTextNode(input_string)
    dc_ele.appendChild(dc_txt)
    return dc_ele

