from utils import serializeText

# Currently, the Dublin Core will only be extended by the OPF Spec
# See http://old.idpf.org/2007/opf/OPF_2.0_final_spec.html#Section2.2

def dc_identifier(mydoc, parent, artmeta):
    '''Create dc:identifer node for OPF'''
    for (_data, _id) in artmeta.identifiers:
        if _id == 'doi':
            newchild = mydoc.createElement('dc:identifier')
            newchild.appendChild(mydoc.createTextNode(_data))
            newchild.setAttribute('id', 'PrimaryID')
            newchild.setAttribute('opf:scheme', 'DOI') #Extended by OPF
            parent.appendChild(newchild)

def dc_title(mydoc, parent, artmeta):
    '''Create dc:title node for OPF'''
    newchild = mydoc.createElement('dc:title')
    title_text = serializeText(artmeta.article_title, stringlist = [])
    newchild.appendChild(mydoc.createTextNode(title_text))
    parent.appendChild(newchild)

def dc_rights(mydoc, parent, artmeta):
    '''Create dc:rights node for OPF'''
    newchild = mydoc.createElement('dc:rights')
    copyright_text = serializeText(artmeta.art_copyright_statement)
    newchild.appendChild(mydoc.createTextNode(copyright_text))
    parent.appendChild(newchild)

def dc_creator(mydoc, parent, artmeta):
    '''Create dc:creator node(s) for OPF'''
    for auth in artmeta.art_auths:
        newchild = mydoc.createElement('dc:creator')
        newchild.appendChild(mydoc.createTextNode(auth.get_name()))
        newchild.setAttribute('opf:role', 'aut') #Extended by OPF
        newchild.setAttribute('opf:file-as', auth.get_fileas_name()) #Extended by OPF
        parent.appendChild(newchild)

def dc_contributor(mydoc, parent, artmeta):
    '''Create dc:contributor node(s) for OPF'''
    for contr in artmeta.art_edits:
        newchild = mydoc.createElement('dc:contributor')
        newchild.appendChild(mydoc.createTextNode(contr.get_name()))
        newchild.setAttribute('opf:role', 'edt')
        newchild.setAttribute('opf:file-as', contr.get_fileas_name())
        parent.appendChild(newchild)
    
    for contr in artmeta.art_other_contrib:
        newchild = mydoc.createElement('dc:contributor')
        newchild.appendChild(mydoc.createTextNode(contr.get_name()))
        newchild.setAttribute('opf:file-as', contr.get_fileas_name())
        parent.appendChild(newchild)

def dc_coverage(mydoc, parent, artmeta):
    '''Create dc:coverage node for OPF'''
    pass    #Do nothing with this tag for now

def dc_date(mydoc, parent, artmeta):
    '''Create dc:date nodes for OPF'''
    try:
        accepted = artmeta.history['accepted']
    except KeyError:
        pass
    else:
        newchild = mydoc.createElement('dc:date')
        datastring = accepted.dateString()
        newchild.appendChild(mydoc.createTextNode(datastring))
        newchild.setAttribute('opf:event', 'creation') # Extended by OPF
        parent.appendChild(newchild)
    
    newchild = mydoc.createElement('dc:date')
    datastring = artmeta.art_dates['epub'].dateString()
    newchild.appendChild(mydoc.createTextNode(datastring))
    newchild.setAttribute('opf:event', 'publication') # Extended by OPF
    parent.appendChild(newchild)
    
    try:
        ecorrected = artmeta.art_dates['ecorrected']
    except KeyError:
        pass
    else:
        newchild = mydoc.createElement('dc:date')
        datastring = ecorrected.dateString()
        newchild.appendChild(mydoc.createTextNode(datastring))
        newchild.setAttribute('opf:event', 'modification') # Extended by OPF
        parent.appendChild(newchild)

def dc_description(mydoc, parent, artmeta):
    '''Create dc:description node for OPF'''
    from utils import serializeText #Recursively extract only TextNode data
    newchild = mydoc.createElement('dc:description')
    #This lists the abstract types in decreasing preference for use in dc:description 
    type_hierarchy = ['default', 'ASCII', 'summary', 'web-summary', 'editor', 
                      'short', 'executive-summary']
    abstract_node = None
    for type in type_hierarchy:
        try:
            abstract_node = artmeta.abstracts[type]
        except KeyError:
            pass
        else:
            break #If we find an appropriate key, break out of the for loop
        
    if abstract_node:
        abstract_text = serializeText(abstract_node, stringlist = [])
        newchild.appendChild(mydoc.createTextNode(abstract_text))
        parent.appendChild(newchild)

def dc_relation(mydoc, parent, artmeta):
    '''Create dc:relation node(s) for OPF'''
    for related in artmeta.related_articles:
        newchild = mydoc.createElement('dc:relation')
        newchild.appendChild(mydoc.createTextNode(related))
        parent.appendChild(newchild)

def dc_source(mydoc, parent, artmeta):
    '''Create dc:source node for OPF'''
    pass    #Do nothing with this tag for now

def dc_subject(mydoc, parent, artmeta):
    '''Create dc:subject node(s) for OPF'''
    from utils import serializeText
    subj_list = []
    try:
        subj_list += artmeta.article_categories.subj_groups['Discipline']
    except KeyError:
        pass
    try:
        subj_list += artmeta.article_categories.subj_groups['Discipline-v2']
    except KeyError:
        pass
    for subject in subj_list:
        newchild = mydoc.createElement('dc:subject')
        subject_text = serializeText(subject, stringlist = [])
        newchild.appendChild(mydoc.createTextNode(subject_text))
        parent.appendChild(newchild)

def dc_format(mydoc, parent):
    '''Create dc:format node(s) for OPF'''
    newchild = mydoc.createElement('dc:format')
    newchild.appendChild(mydoc.createTextNode('application/epub+zip'))
    parent.appendChild(newchild)

def dc_type(mydoc, parent, artmeta):
    '''Creates dc:type node for OPF'''
    #Recommended best practice is to use a controlled vocabulary such as:
    #http://dublincore.org/documents/dcmi-type-vocabulary/
    #This is implemented here:
    newchild = mydoc.createElement('dc:type')
    datastring = 'text'
    newchild.appendChild(mydoc.createTextNode(datastring))
    parent.appendChild(newchild)
    
    #An alternative implementation might utilize the "heading" subject group:
    #newchild = mydoc.createElement('dc:type')
    #datastring = artmeta.article_categories.subj_groups['heading'][0]
    #newchild.appendChild(mydoc.createTextNode(datastring))
    #parent.appendChild(newchild)

def dc_language(mydoc, parent):
    '''Creates dc:language for OPF'''
    newchild = mydoc.createElement('dc:language')
    newchild.appendChild(mydoc.createTextNode('en')) # Presume en for now
    parent.appendChild(newchild)

def generateDCMetadata(mydoc, opfmetanode, artmeta, jrnmeta):
    '''The method for generating all the Dublin Core metadata tags 
    which are to be created in the OPF document under the metadata node.
    '''
    parent = opfmetanode
    
    dc_identifier(mydoc, parent, artmeta)
    dc_title(mydoc, parent, artmeta)
    dc_rights(mydoc, parent, artmeta)
    dc_creator(mydoc, parent, artmeta)
    dc_contributor(mydoc, parent, artmeta)
    dc_coverage(mydoc, parent, artmeta)
    dc_date(mydoc, parent, artmeta)
    dc_description(mydoc, parent, artmeta)
    dc_relation(mydoc, parent, artmeta)
    dc_source(mydoc, parent, artmeta)
    dc_subject(mydoc, parent, artmeta)
    dc_format(mydoc, parent) # Format is epub, independent of input
    dc_type(mydoc, parent, artmeta)
    dc_language(mydoc, parent)