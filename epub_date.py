"""Module to handle dates from the Journal Publishing tag set
<date> Element: http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-kh50.html
<pub-date>: http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-d8x0.html
Citation elements also require date information
"""

import datetime

class DateInfo(object):
    """Date with extra info
    datenode -- the XML Element containing the date info
    """
    def __init__(self, datenode):
        self.type = ''
        self.season = ''
        self.date = None
        
        year, month, day = self.parse(datenode)
        self.date = datetime.date(year, month, day)
    
    def parse(self, datenode):
        """Handle the node contents
        datenode -- the XML Element containing the date info
        returns a 3-tuple: (year, month, day)
        """
        # set some defaults
        year = 0
        month = 1
        day = 1
        
        if datenode.tagName == 'date':
            self.type = datenode.getAttribute('date-type')
        elif datenode.tagName == 'pub-date':
            self.type = datenode.getAttribute('pub-type')
        
        child = datenode.firstChild
        if child.tagName == 'season':
            self.season = child.firstChild.data
        elif child.tagName == 'day':
            day = int(child.firstChild.data)
            if child.nextSibling:
                month = int(child.nextSibling.firstChild.data)
        elif child.tagName == 'month':
            month = int(child.firstChild.data)
        
        # year is always the last element
        child = datenode.lastChild
        year = int(child.firstChild.data)
        
        return (year, month, day)