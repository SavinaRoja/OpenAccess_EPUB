OpenAccess_EPUB is a program for converting OpenAccess Academic Journal
articles into the ePub format.

This program is currently being developed to support PLoS and Frontiers
journals but is designed with the addition of new journal support in mind.

Getting Started
---------------
Nicer documentation for users wishing to use the program is on the wiki:
https://github.com/SavinaRoja/OpenAccess_EPUB/wiki

This program is developed in Python 2.7. It probably won't work in Python 3
but I'll get to that someday

sudo python setup.py install

For Mac and Windows, enter:

python setup.py install

Windows systems may require additional configuration (see the wiki). Now you
may begin to use the program by typing "oaepub" at the command-line. The basic
input for the program is always an XML file for the article you wish to
convert. One way to find this is the side bar of any Frontiers or PLoS article
web page. After downloading it, navigate by command-line to that directory and
try:

oaepub -i your-xml-file.xml

How to Contribute
-----------------
If you would like to contribute to the project, there are many ways to do so. 
If you know Python and would like to assist in development, contact me and we 
can discuss how you may help. Feedback regarding bugs, presentation, formatting,
and accessibility are all quite valuable.

Author
------
Paul Barton (SavinaRoja)
