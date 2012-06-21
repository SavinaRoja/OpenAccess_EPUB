"""
This is the setup file to install OpenAccess_EPUB.
"""

from distutils.core import setup
import os.path

#If you change this behavior, make sure you also change the defaults in
#settings.py
static = os.path.join(os.path.expanduser('~'), '.OpenAccess_EPUB')

setup(name='OpenAccess_EPUB',
      version='0.2.0',
      description='Converts OpenAccess Journal articles to ePub',
      author='Paul Barton',
      author_email='pablo.barton@gmail.com',
      url='https://github.com/SavinaRoja/OpenAccess_EPUB',
      package_dir={'': 'src'},
      packages=['OpenAccess_EPUB', 'OpenAccess_EPUB.dublincore',
                'OpenAccess_EPUB.jpts', 'OpenAccess_EPUB.ncx',
                'OpenAccess_EPUB.opf', 'OpenAccess_EPUB.ops',
                'OpenAccess_EPUB.settings', 'OpenAccess_EPUB.utils'],
      scripts=['scripts/oaepub'],
      data_files=[(os.path.join(static, 'resources'), ['resources/text.css'])]
      )
