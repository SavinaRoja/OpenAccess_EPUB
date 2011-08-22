class JournalMeta(object):
    '''
    Journal-level metadata
    journal_meta_node -- XML node containing journal metadata
    '''
    def __init__(self, journal_meta_node):
        self.source = journal_meta_node
        self.identifier = {}
        self.title = []
        self.title_abbr = []
        self.issn = {}
        self.publisher = None
        self.notes = None
        self.identify(journal_meta_node)
        self.notes_status = False
    
    def identify(self, journal_meta_node):
        '''process metadata'''
        # Collect a list of all journal-title nodes
        journal_title = journal_meta_node.getElementsByTagName('journal-title')
        
        # Extract title strings from journal-title nodes into self.title list
        for jrn_tit in journal_title:
            self.title.append(jrn_tit.firstChild.data)
        
        # Collect a list of all abbrev-journal-title nodes
        abbr_titles = 'abbrev-journal-title'
        abbrev_titles = journal_meta_node.getElementsByTagName(abbr_titles)
        
        # Extract abbreviated title strings
        for abbr_jrn_tit in abbrev_titles:
            self.title_abbr.append(abbr_jrn_tit.firstChild.data)

        # Collect a list of all ISSN nodes
        issns = journal_meta_node.getElementsByTagName('issn')

        # enter ISSNs into self.issn with associated pub-type strings
        for item in issns:
            issn_id = item.firstChild.data
            self.issn[issn_id] = item.getAttribute('pub-type')
            
        # Collect a list of all journal-id nodes
        journal_id = journal_meta_node.getElementsByTagName('journal-id')
        
        # enter journal-ids into self.identifier with associated
        # journal-id-type strings
        for jid in journal_id:
            jrn_id_type = jid.getAttribute('journal-id-type')
            self.identifier[jrn_id_type] = jid.firstChild.data

        # Create a notes node, if such exists
        notes = journal_meta_node.getElementsByTagName('notes')
        if notes:
            self.notes_status = True
                
        # Collect the publisher node
        publisher_node = journal_meta_node.getElementsByTagName('publisher')[0]
        
        # Instantiate an instance of Publisher(node)
        self.publisher = Publisher(publisher_node)
        
    def __str__(self):
        tmpstr = 'Journal Title(s):{0} |Abbreviated Title(s):{1} |Journal IDs:'
        tmpstr = tmpstr + '{2}|ISSNs: {3} |Notes?: {4} |Publisher: {5}'
        titlestr = u''
        for title in self.title:
            titlestr = titlestr + ' ' + title
            
        abbrtitlestr = u''
        for abbrtitle in self.title_abbr:
            abbrtitlestr = abbrtitlestr + '' + abbrtitle
        
        jidstr = u''
        for key, value in self.identifier.iteritems():
            jidstr = jidstr + key + '; ' + value + ', '

        issnstr = u''
        for key, value in self.issn.iteritems():
            issnstr = issnstr + key + '; ' + value + ', '
        
        pubstr = self.publisher.__str__()
        outstr = tmpstr.format(titlestr,
                               abbrtitlestr,
                               jidstr,
                               issnstr,
                               self.notes_status,
                               pubstr)
        return outstr

class Publisher(object):
    '''
    Publisher information
    node -- publisher node from an XML document object
    '''
    def __init__(self, publisher_node):
        self.name = u''
        self.location = u''
        self.identify(publisher_node)
    
    def identify(self, publisher_node):
        '''Pulls info from the xml'''
        tmp = publisher_node.getElementsByTagName('publisher-name')[0]
        self.name = tmp.firstChild.data
        tmp = publisher_node.getElementsByTagName('publisher-loc')[0]
        self.location = tmp.firstChild.data
        
    def __str__(self):
        pubstring = 'Publisher Name: {0}, Publisher Location: {1}'
        retstr = pubstring.format(self.name, self.location)
        return retstr
