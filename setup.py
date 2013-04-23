"""
This is the setup file to install openaccess_epub.
"""

from distutils.core import setup

setup(name='openaccess_epub',
      version='0.3.0',
      description='Converts OpenAccess Journal articles to ePub',
      author='Paul Barton',
      author_email='pablo.barton@gmail.com',
      url='https://github.com/SavinaRoja/openaccess_epub',
      package_dir={'': 'src'},
      packages=['openaccess_epub', 'openaccess_epub.dublincore',
                'openaccess_epub.jpts', 'openaccess_epub.ncx',
                'openaccess_epub.opf', 'openaccess_epub.ops',
                'openaccess_epub.settings', 'openaccess_epub.utils'],
      scripts=['scripts/oaepub', 'scripts/epubzip'],
      data_files=[]
      )
