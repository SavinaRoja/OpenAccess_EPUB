"""
This is the setup file to install openaccess_epub.
"""

from distutils.core import setup
#from setuptools import setup


def long_description():
    with open('README.md', 'r') as readme:
        readme_text = readme.read()
    return(readme_text)

setup(name='openaccess_epub',
      version='0.6.2',
      description='Converts OpenAccess Journal articles to EPUB',
      long_description=long_description(),
      author='Paul Barton',
      author_email='pablo.barton@gmail.com',
      url='https://github.com/SavinaRoja/openaccess_epub',
      package_dir={'': 'src'},
      packages=['openaccess_epub',
                'openaccess_epub.article',
                'openaccess_epub.commands',
                'openaccess_epub.navigation',
                'openaccess_epub.package',
                'openaccess_epub.publisher',
                'openaccess_epub.utils'],
      package_data={'openaccess_epub': ['data/dtds/*/*.*',
                                        'data/dtds/*/*/*.*']},
      scripts=['scripts/oaepub'],
      data_files=[('', ['README.md'])],
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Other Audience',
                   'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                   'Programming Language :: Python :: 3',
                   'Operating System :: OS Independent',
                   'Topic :: Text Processing :: Markup :: XML',
                   'Topic :: Other/Nonlisted Topic'],
      install_requires=['docopt', 'lxml']
      )
