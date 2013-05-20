# -*- coding: utf-8 -*-
"""
For the creation of default CSS files.
"""

DEFAULT_CSS='''/*A default CSS page, developed while working on PLoS*/

/*Some divs are classed for special treatment*/
div.abstract,
div.editorsAbstract,
div.summary,
div.articleInfo {
    padding:0 10px;
    margin:20px 0 40px 0;
    border-left:5px solid #CCE3F6;
}

/*The ArticleInfo is a special segment of an article, it contains content that
should be distinguishable from the main text.*/
#ArticleInfo {
    border-top: 1px dashed;
    border-bottom: 1px dashed;
}

/**/
span.footnote {
    display:block;
}

/*The disp-quote is for extended quotations, extracts, etc. they should be
notably separate in display from the main text body.*/
.disp-quote {
    display:block;
    margin-left:5%;
}

/*The common forms of images in articles are figures, formulas, and tables;
Special style rules for these img elements go here.*/
/*disp-formula*/
img.disp-formula {
    display:block;
}
b.disp-formula-label {
    display:block;
    text-align:right;
}
/*figure*/
img.figure {
    display:block;
    margin-left:auto;
    margin-right:auto;
}
/*table*/
img.table {
    display:block;
    margin-left:auto;
    margin-right:auto;

/*Rules for boxed-text*/
div.boxed-text {
    margin:5%;
    background-color:#EEEEEE;
}

/*Rules for verse-line*/
p.verse-line {
    font-style:italic;
    line-height:50%;
}

/*Rules for definition lists*/
p.def-item-term {
    font-weight:bold;
}
p.def-item-def {
    font-style:italic;
    margin-left:5%;
}

/*These are for the handling of lists, to give them the appropriate list item
indicators.*/
ul.simple {
    list-style-type:none;
}
ol.alpha-lower {
    list-style-type:lower-alpha;
}
ol.alpha-upper {
    list-style-type:upper-alpha;
}
ol.roman-lower {
    list-style-type:lower-roman;
}
ol.roman_upper {
    list-style-type:upper-roman;
}'''