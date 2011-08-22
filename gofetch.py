"""fetch article images"""
import urllib2
import logging
import os.path

def getimages(fm, dirname):
    """fetch article images"""
    for (_data, _id) in fm.article_meta.identifiers:
        if _id == 'doi':
            doidata = _data
    
    slashsplit = doidata.split('/')
    journaldoi = slashsplit[0]
    dotsplit = slashsplit[1].split('.')
    journalid = dotsplit[1]
    articledoi = dotsplit[2]
    
    if journalid == 'pgen':
        journalurl = 'http://www.plosgenetics.org/'
    elif journalid == 'pcbi':
        journalurl = 'http://www.ploscompbiol.org/'
    elif journalid == 'ppat':
        journalurl = 'http://www.plospathogens.org/'
    elif journalid == 'pntd':
        journalurl = 'http://www.plosntds.org/'
    elif journalid == 'pmed':
        journalurl = 'http://www.plosmedicine.org/'
    elif journalid == 'pbio':
        journalurl = 'http://www.plosbiology.org/'
    elif journalid == 'pone':
        journalurl = 'http://www.plosone.org/'
        
    plosstring = 'article/fetchObject.action?uri=info%3Adoi%2F'
    
    imagetypes = ['g', 't', 'e']
    
    for itype in imagetypes:
        if itype == 'g':
            subdirect = 'figures'
        elif itype == 't':
            subdirect = 'tables'
        elif itype == 'e':
            subdirect = 'equations'
        refnum = 1
        while refnum < 1000:
            addr_str = '{0}{1}{2}%2Fjournal.{3}.{4}.{5}{6}&representation=PNG_L'
            address = addr_str.format(journalurl, plosstring, journaldoi,
                                      journalid, articledoi, itype,
                                      str(refnum).zfill(3))
            try:
                print(address)
                if itype == 'e':
                    address = address[0:-2]
                image = urllib2.urlopen(address)
                filename = '{0}{1}.png'.format(itype, str(refnum).zfill(3))
                image_file = os.path.join(dirname, 'OPS', 'images',
                                          subdirect, filename)
                with open(image_file, 'wb') as outimage:
                    outimage.write(image.read())
                
            except urllib2.HTTPError:
                logging.debug('reached the end of that type')
                break
            refnum += 1
