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
        
        if datenode.tagName == 'date':
            self.type = datenode.getAttribute('date-type')
        elif datenode.tagName == 'pub-date':
            self.type = datenode.getAttribute('pub-type')
        
        try:
            self.season = datenode.getElementsByTagName('season')[0].firstChild.data
        except IndexError:
            try:
                day = int(datenode.getElementsByTagName('day')[0].firstChild.data)
            except IndexError:
                day = 1
            try:
                month = int(datenode.getElementsByTagName('month')[0].firstChild.data)
            except IndexError:
                month = 1
        
        year = int(datenode.getElementsByTagName('year')[0].firstChild.data)
        
        return (year, month, day)