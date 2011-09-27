import utils
    
def generateTOC(fm, features):
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
    
    def navmapper(featurenode, navpoint):
        for child in featurenode.childNodes:
            if child.tagName == 'sec':
                navnode = doc.createElement('navPoint')
                navpoint.appendChild(navnode)
                navnode.setAttribute('playOrder',child.getAttribute('playOrder'))
                navnode.setAttribute('id', child.getAttribute('id'))
                titlenode = child.getElementsByTagName('title')[0]
                titletext = utils.serializeText(titlenode, stringlist = [])
                navlabel = doc.createElement('navLabel')
                navnode.appendChild(navlabel)
                navlabel.appendChild(makeText(titletext))
                content = doc.createElement('content')
                content.setAttribute('src', 'article.xml#{0}'.format(child.getAttribute('id')))
                navnode.appendChild(content)
                navmapper(child, navnode)
    
    def listFigures(featurenode, navpoint):
        for child in featurenode.getElementsByTagName('fig'):
            navtarget = doc.createElement('navTarget')
            navtarget.setAttribute('class', 'figure')
            navtarget.setAttribute('playOrder',child.getAttribute('playOrder'))
            navtarget.setAttribute('id', child.getAttribute('id'))
            navlabel = doc.createElement('navLabel')
            titlenode = child.getElementsByTagName('title')[0]
            titletext = utils.serializeText(titlenode, stringlist = [])
            navlabel.appendChild(makeText(titletext))
            navtarget.appendChild(navlabel)
            content = doc.createElement('content')
            content.setAttribute('src', '')
            navtarget.appendChild(content)
            navpoint.appendChild(navtarget)
            
    def listTables(featurenode, navpoint):
        for child in featurenode.getElementsByTagName('table'):
            navtarget = doc.createElement('navTarget')
            navtarget.setAttribute('class', 'table')
            navlabel = doc.createElement('navLabel')
            titlenode = child.getElementsByTagName('title')[0]
            titletext = utils.serializeText(titlenode, stringlist = [])
            navlabel.appendChild(makeText(titletext))
            navtarget.appendChild(navlabel)
            content = doc.createElement('content')
            content.setAttribute('src', '')
            navtarget.appendChild(content)
            navpoint.appendChild(navtarget)
            
    def listEquations(featurenode, navpoint):
        children = featurenode.getElementsByTagName('inline-formula')
        children += featurenode.getElementsByTagName('disp-formula')
        for child in children:
            navtarget = doc.createElement('navTarget')
            navtarget.setAttribute('class', 'equation')
            navlabel = doc.createElement('navLabel')
            titlenode = child.getElementsByTagName('title')[0]
            titletext = utils.serializeText(titlenode, stringlist = [])
            navlabel.appendChild(makeText(titletext))
            navtarget.appendChild(navlabel)
            content = doc.createElement('content')
            content.setAttribute('src', '')
            navtarget.appendChild(content)
            navpoint.appendChild(navtarget)
    
    ncx = doc.lastChild #IGNORE:E1101
    ncx.setAttribute('version', '2005-1')
    ncx.setAttribute('xml:lang', 'en-US')
    ncx.setAttribute('xmlns', 'http://www.daisy.org/z3986/2005/ncx/')
    
    ncx_elements = ['head', 'docTitle', 'docAuthor', 'navMap']
    for element in ncx_elements:
        ncx.appendChild(doc.createElement(element))
    head, doctitle, docauthor, navmap = ncx.childNodes
    
    if features.getElementsByTagName('fig'):
        lof = doc.createElement('navList')
        lof.setAttribute('id', 'lof')
        lof.setAttribute('class', 'lof')
        navlabel = doc.createElement('navLabel')
        lof.appendChild(navlabel)
        navlabel.appendChild(makeText('List of Figures'))
        ncx.appendChild(lof)
        #Create the navList element for the list of figures
        listFigures(features, lof)
    
    if features.getElementsByTagName('table'):
        lot = doc.createElement('navList')
        lot.setAttribute('id', 'lot')
        lot.setAttribute('class', 'lot')
        navlabel = doc.createElement('navLabel')
        lot.appendChild(navlabel)
        navlabel.appendChild(makeText('List of Tables'))
        ncx.appendChild(lot)
        #Create the navList element for the list of tables
        listTables(features, lot)
        
    if features.getElementsByTagName('inline-formula') or features.getElementsByTagName('disp-formula'):
        loe = doc.createElement('navList')
        loe.setAttribute('id', 'loe')
        loe.setAttribute('class', 'loe')
        navlabel = doc.createElement('navLabel')
        loe.appendChild(navlabel)
        navlabel.appendChild(makeText('List of Equations'))
        ncx.appendChild(lot)
        #Create the navList element for the list of equations
        listEquations(features, loe)
        
    
    statement = doc.createComment('''The following metadata items, except for dtb:generator,
            are required for all NCX documents, including those 
            conforming to the relaxed constraints of OPS 2.0''')
    head.appendChild(statement)
    
    metas = []
    #For now, the global unique identifier will utilize the DOI
    for (_data, _id) in fm.article_meta.identifiers:
        if _id == 'doi':
            metas.append(metatag('dtb:uid', _data))
    
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
    
    tocname = 'NCX for: {0}'.format(fm.article_meta.title)
    doctitle.appendChild(makeText(tocname))
    docauthor.appendChild(makeText('{0}{1}'.format('Primary author: ', 
                                                   fm.article_meta.art_auths[0].get_name())))
    
    #Create the navMap element
    navlabel = doc.createElement('navLabel')
    navmap.appendChild(navlabel)
    navlabel.appendChild(makeText('Table of Contents'))
    navmapper(features, navmap)
    
    outdoc = open('{0}/OPS/toc.ncx'.format(utils.OUT_DIR),'w')
    outdoc.write(doc.toprettyxml(encoding = 'UTF-8'))
    outdoc.close()