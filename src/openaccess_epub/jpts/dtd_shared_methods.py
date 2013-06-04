# -*- coding: utf-8 -*-
"""
This is an experimental submodule while I work on revising the JPTS metadata
work. Its basic goal is to provide a single definition point for methods that
are shared by some DTD versions, but not all.
"""

import openaccess_epub.utils.element_methods as element_methods

def extract_journal_title(self):
    """
    For JPTS DTD versions 2.0, 2.1, and 2.2:

    <journal-title> is an optional element, zero or more, under <journal-meta>
    It can only contain text, numbers, or special characters. It has no
    attributes, and thus returns only a list of strings for titles.
    """
    journal_titles = []
    for title in self.journal_meta.getElementsByTagName('journal-title'):
        journal_titles.append(element_methods.node_text(title))
    return journal_titles

extract_journal_title_20 = extract_journal_title
extract_journal_title_21 = extract_journal_title
extract_journal_title_22 = extract_journal_title

def extract_journal_title(self):
    """
    For JPTS DTD versions 2.3, and 3.0:

    <journal-title> is an optional element, zero or more, under <journal-meta>
    It can only contain text, numbers, or special characters. It has one
    attribute, content-type.
    """
    journal_titles = []
    for title in self.journal_meta.getElementsByTagName('journal-title'):
        journal_titles.append(element_methods.node_text(title))
    return journal_titles