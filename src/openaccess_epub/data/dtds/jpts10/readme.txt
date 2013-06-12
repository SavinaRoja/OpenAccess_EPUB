README.TXT                               March 2003

This README names the modules delivered as Version 1.0 
of the Journal Publishing DTD, including the necessary
portions of Version 1.0 of the Archiving and Interchange 
DTD Suite.         

The rest of this README contains notes concerning:
  1.0 File Names
  2.0 Modules Specific to the Journal Publishing DTD
  3.0 Archiving and Interchange DTD Suite Modules Used
        in this DTD
      3.1 Element Class Modules
      3.2 Math Modules 
      3.3 Table Modules
      3.4 Notations and Special Characters


------------------------------------------------------
1.0 File Names

catalog.ent - OASIS SOCAT catalog of the formal public
              identifier (fpi) and file names for each
              DTD and module.
              Not part of the DTD or the Suite proper, but 
              used to implement a system using the suite.


------------------------------------------------------
2.0 Modules Specific to the Journal Publishing DTD

journalpublishing.dtd          
             - The DTD file for the Journal Publishing 
               DTD. The DOCTYPE in this DTD covers a 
               journal article and various other 
               non-article journal content such as book 
               and product reviews. This DTD invokes 
               almost all the modules in the Archiving 
               and Interchange DTD Suite, changing their
               element contents and attributes as necessary
               using the Customization module

journalpubcustomize.ent 
             - The customization module. This is the
               secondary DTD module that, with the DTD
               itself, makes up the Journal Publishing
               DTD. This module defines the classes, 
               mixes, and Parameter Entities for 
               this specific journal authoring and first
               XML tagging DTD. (Called as the second 
               module in the DTD, after the module that 
               names the modules, modules.ent.)
 

------------------------------------------------------
3.0 Archiving and Interchange DTD Suite Modules Used
      in this DTD

modules.ent      - Names all the modules in the
                   Archiving and Interchange DTD Suite.
                   (Called as the first module by
                   the Journal Publishing DTD.)

common.ent       - Defines all elements, attributes, 
                   entities, attribute values that are
                   used by more than one module in the
                   full Suite. (Called as the third 
                   module by the Journal Publishing DTD.)

These modules are invoked before all other modules 
in this DTD. Other modules can usually be invoked in any order,
and are invoked in alphabetical order.


------------------------------------------------------
3.1 Element Class Modules (define elements, attributes 
      for a single element class)

articlemeta.ent  - Article-level metadata elements 
backmatter.ent   - Article-level back matter elements
display.ent      - Display elements such as Table, Figure, 
                     Graphic
format.ent       - Format-related elements such as Bold
journalmeta.ent  - Journal-level metadata elements
link.ent         - Linking elements such as 
                     X(Cross)-Reference
list.ent         - List elements
math.ent         - Suite-defined math elements such as 
                     Display Equation
para.ent         - Paragraph-level elements such as 
                     Paragraph and Display Quote
phrase.ent       - Phrase-level content-related elements
references.ent   - Bibliographic reference list and the 
                     elements that can be used inside a 
                     citation
section.ent      - Section-level elements


------------------------------------------------------
3.2 Math Modules (Define MathML tagging, used in math.ent)

mathml2.dtd
mathmlsetup.ent

And inside the mathml subdirectory:
  mathml2-qname-1.mod
  mmlalias.ent
  mmlextra.ent

 
------------------------------------------------------
3.3 Table Modules (Define XHTML Table Model)

Using the XHTML table model requires two modules: one to set 
up the Parameter Entities necessary to use the model, and the 
second to define the table model itself (as defined publicly).

Archiving and Interchange DTD Suite version (no namespaces) 
of the XHTML Table Model
  XHTMLtablesetup.ent (setup module)
  htmltable.dtd       (PUBLIC module)


------------------------------------------------------
3.4 Notations and Special Characters

notat.ent        - Names all notations used
xmlspecchars.ent - Names all the standard special character
                      entity sets to be used by the DTD. The
                      MathML characters sets were used,
                      unchanged
chars.ent        - Definitions of DTD-specific and custom
                      special characters (as general entities
                      defined as hexadecimal or decimal character
                      entities - Unicode numbers or using the
                      <private-char> element.) 

All the MathML special character entity sets
(inside the xmlchars subdirectory)
  isoamsa.ent
  isoamsb.ent
  isoamsc.ent
  isoamsn.ent
  isoamso.ent
  isoamsr.ent
  isobox.ent
  isocyr1.ent
  isocyr2.ent
  isodia.ent
  isogrk1.ent
  isogrk2.ent
  isogrk3.ent
  isogrk4.ent
  isolat1.ent
  isolat2.ent
  isomfrk.ent
  isomopf.ent
  isomscr.ent
  isonum.ent
  isopub.ent
  isotech.ent

------------ document end ----------------------------



