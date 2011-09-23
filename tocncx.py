import utils
    
def generateTOC(fm):
    '''Used to generate the table of contents for the article. Should be
    kept in accordance with the Daisy Talking Book specification.'''
    
    #Different construction than found in utils.initiateDocument()
    _publicId = '-//NISO//DTD ncx 2005-1//EN'
    _systemId = 'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'
    
    from xml.dom.minidom import getDOMImplementation
    
    impl = getDOMImplementation()
    
    mytype = impl.createDocumentType('ncx', _publicId, _systemId)
    doc = impl.createDocument(None, 'ncx', mytype)
    
    def metatag(_name, _content):
        meta = doc.createElement('meta')
        meta.setAttribute('name', _name)
        meta.setAttribute('content', _content)
        return meta
    
    def makeText(textstring):
        text = doc.createElement('text')
        text.appendChild(doc.createTextNode(textstring))
        return text

    
    root = doc.lastChild #IGNORE:E1101
    ncx = doc.createElement('ncx')
    ncx.setAttribute('version', '2005-1')
    ncx.setAttribute('xml:lang', 'en-US')
    ncx.setAttribute('xmlns', 'http://www.daisy.org/z3986/2005/Z3986-2005.html')
    root.appendChild(ncx)
    
    head = doc.createElement('head')
    statement = doc.createComment('''The following metadata items, except for dtb:generator,
            are required for all NCX documents, including those 
            conforming to the relaxed constraints of OPS 2.0''')
    
    head.appendChild(statement)
    
    metas = []
    #For now, the global unique identifier will utilize the DOI
    for (_data, _id) in fm.article_meta.identifiers:
        if _id == 'doi':
            doidata = _data
    metas.append(metatag('dtb:uid', doidata))
    
    # NCX Depth of the document
    metas.append(metatag('dtb:depth', '2'))
    
    # Non-negative integer indicating the number of pageTargets in the pageList
    metas.append(metatag('dtb:totalPageCount', '0'))
    
    # Non-negative integer indicating the largest value attribute on
    # pageTarget in the pageList.
    metas.append(metatag('dtb:maxPageNumber', '0'))
    
    # Name and version of software that generated the NCX
    metas.append(metatag('dtb:generator', 'openaccess_epub, indev'))
    
    for meta in metas:
        head.appendChild(meta)
    
    root.appendChild(head)
    
    docTitle = doc.createElement('docTitle')
    tocname = 'NCX for: {0}'.format(fm.article_meta.title)
    docTitle.appendChild(makeText(tocname))
    root.appendChild(docTitle)
    
    navmap = doc.createElement('navMap')
    root.appendChild(navmap)
    
    navlist = doc.createElement('navList')
    root.appendChild(navlist)
    
    outdoc = open('{0}/toc.ncx'.format(utils.OUT_DIR),'w')
    outdoc.write(doc.toprettyxml(encoding = 'UTF-8'))
    outdoc.close()