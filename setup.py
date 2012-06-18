"""
This is the setup file to install OpenAccess_EPUB.
"""

from distutils.core import setup

setup(name='OpenAccess_EPUB',
      version='0.2.0',
      description='Converts OpenAccess Journal articles to ePub',
      author='Paul Barton',
      author_email='pablo.barton@gmail.com',
      url='https://github.com/SavinaRoja/OpenAccess_EPUB',
      package_dir={'': 'src'},
      packages=['OpenAccess_EPUB']
      )
