# -*- coding: utf-8 -*-

from lxml import etree

def transform_person_group(person_group, mode):
    transform = ''
    
    def make_persons_in_mode():
        given_names = citation.xpath('string(descendant::given-names)')
        