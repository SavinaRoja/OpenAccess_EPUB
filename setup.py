"""
This is the setup file to install openaccess_epub.
"""

from distutils.core import setup

def long_description():
    with open('README.md', 'r') as readme:
        readme_text = readme.read()
    return(readme_text)

setup(name='openaccess_epub',
      version='0.3.8',
      description='Converts OpenAccess Journal articles to ePub',
      long_description=long_description(),
      author='Paul Barton',
      author_email='pablo.barton@gmail.com',
      url='https://github.com/SavinaRoja/openaccess_epub',
      package_dir={'': 'src'},
      packages=['openaccess_epub', 'openaccess_epub.jpts',
                'openaccess_epub.ncx', 'openaccess_epub.opf',
                'openaccess_epub.ops', 'openaccess_epub.utils'],
      scripts=['scripts/oaepub', 'scripts/epubzip', 'scripts/oae-quickstart'],
      data_files=[]
      )
