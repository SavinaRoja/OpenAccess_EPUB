import utils

class Back(object):
    
    def __init__(self, node):
        self.footnotes = node.getElementsByTagName('fn')
        self.funding = None
        self.competing_interests = None
        for item in self.footnotes:
            if item.getAttribute('fn-type') == u'conflict':
                text = utils.serializeText(item, stringlist = [])
                self.competing_interests = text
            elif item.getAttribute('fn-type') == u'financial-disclosure':
                text = utils.serializeText(item, stringlist = [])
                self.funding = text