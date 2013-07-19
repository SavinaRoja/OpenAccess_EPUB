<?xml version="1.0" encoding="UTF-8"?><!-- 1/4/12: nlm contains xml version, we added encoding -->

<!-- 1/4/12: plos-specific stylesheet. contains plos-specific templates and modified nlm templates. imports and overrides nlm. -->

<!-- 1/4/12: nlm contains informational comments (system, purpose, input, output) -->

<!-- 1/4/12: plos modifications -->
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:util="http://dtd.nlm.nih.gov/xsl/util"
    xmlns:mml="http://www.w3.org/1998/Math/MathML"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:aml="http://topazproject.org/aml/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    exclude-result-prefixes="util xsl xlink mml xs aml dc">

    <!-- 1/4/12: plos-specific instruction. import nlm -->
    <xsl:import href="jpub3-html.xsl"/>

    <!-- 1/4/12: plos modifications, we output doctype statement via templates -->
    <xsl:output doctype-public=" " doctype-system=" "
        method="html"
        indent="no"
        encoding="UTF-8"
        omit-xml-declaration="yes"/>

    <!-- 1/4/12: nlm contains strip-space, preserve-space, param (css), and keys (element-by-id, xref-by-rid) -->

    <!-- 1/4/12: plos-specific global param (pub config, passed into stylesheet from elsewhere in the pipeline) -->
    <xsl:param name="pubAppContext" />

    <!-- ============================================================= -->
    <!--  ROOT TEMPLATE - HANDLES HTML FRAMEWORK                       -->
    <!-- ============================================================= -->

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="/">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="make-html-header" />

    <!-- ============================================================= -->
    <!--  TOP LEVEL                                                    -->
    <!-- ============================================================= -->

    <!-- 1/4/12: nlm contains template article, which calls make-article -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="sub-article | response" />

    <!-- ============================================================= -->
    <!--  "make-article" for the document architecture                 -->
    <!-- ============================================================= -->

    <!-- 1/4/12: plos modifications -->
    <xsl:template name="make-article">
      <xsl:call-template name="newline2"/>
      <xsl:call-template name="newline1"/>
      <xsl:call-template name="make-front"/>
      <xsl:call-template name="newline1"/>
      <div class="articleinfo">
        <xsl:call-template name="make-article-meta"/>
      </div>
      <xsl:call-template name="make-editors-summary"/>
      <xsl:call-template name="newline2"/>
      <xsl:call-template name="newline1"/>
      <xsl:call-template name="make-body"/>
      <xsl:call-template name="newline1"/>
      <xsl:call-template name="newline1"/>
      <xsl:call-template name="make-back"/>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use (we replace with make-front) -->
    <xsl:template match="front | front-stub" />

    <!-- 1/4/12: plos-specific template (creates author byline, affiliations, abstracts)  -->
    <xsl:template name="make-front">
      <xsl:call-template name="newline1"/>
      <!-- change context to front/article-meta -->
      <xsl:for-each select="front/article-meta">
        <xsl:apply-templates select="title-group" mode="metadata"/>
        <!-- abstracts -->
        <xsl:for-each select="abstract[not(@abstract-type) or (@abstract-type !='toc' and @abstract-type != 'teaser'
             and @abstract-type != 'editor' and @abstract-type != 'patient')]">
          <div class="abstract">
            <xsl:call-template name="abstract-title"/>
            <xsl:apply-templates select="*[not(self::title)]"/>
          </div>
        </xsl:for-each>
      </xsl:for-each>
      <xsl:call-template name="newline2"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates article metadata) -->
    <xsl:template name="make-article-meta">
      <xsl:for-each select="front/article-meta">
        <!-- article citation -->
        <p>
          <strong>Citation: </strong>
          <!-- authors -->
          <xsl:for-each select="contrib-group/contrib[@contrib-type='author'][position() &lt; 7]">
            <xsl:choose>
              <xsl:when test="position() = 6">
                <xsl:text>et al. </xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:choose>
                  <xsl:when test="collab">
                     <xsl:apply-templates select="collab"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <!-- 1/4/12: we'll need to adjust this when we add name-style eastern-->
                    <xsl:apply-templates select="name/surname"/>
                    <xsl:if test="name/given-names">
                      <xsl:text> </xsl:text>
                    </xsl:if>
                    <xsl:call-template name="makeInitials">
                      <xsl:with-param name="x"><xsl:value-of select="name/given-names"/></xsl:with-param>
                    </xsl:call-template>
                  <!-- don't include the period following the suffix -->
                  <xsl:if test="string-length(name/suffix) > 0">
                    <xsl:text> </xsl:text>
                    <xsl:choose>
                      <xsl:when test="substring(name/suffix,string-length(name/suffix))='.'">
                        <xsl:value-of select="substring(name/suffix,1,string-length(name/suffix)-1)"/>
                      </xsl:when>
                      <xsl:otherwise>
                        <xsl:value-of select="name/suffix"/>
                      </xsl:otherwise>
                    </xsl:choose>
                  </xsl:if>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="position() != last()">
                  <xsl:text>, </xsl:text>
                </xsl:if>
               </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
          <!-- pub year -->
          <xsl:text> (</xsl:text>
          <xsl:value-of select="pub-date[@pub-type='collection']/year | pub-date[@pub-type='ppub']/year"/>
          <xsl:text>) </xsl:text>
          <!-- article title -->
          <xsl:apply-templates select="title-group/article-title" mode="metadata-citation"/>
          <xsl:variable name="at" select="normalize-space(title-group/article-title)"/>
          <!-- add a period unless there's other valid punctuation -->
          <xsl:if test="substring($at,string-length($at))!='?' and substring($at,string-length($at))!='!' and substring($at,string-length($at))!='.'">
            <xsl:text>.</xsl:text>
          </xsl:if>
          <xsl:text> </xsl:text>
          <!-- journal/volume/issue/enumber/doi -->
          <xsl:value-of select="../journal-meta/journal-id[@journal-id-type='nlm-ta']"/>
          <xsl:text> </xsl:text>
          <xsl:value-of select="volume"/>(<xsl:value-of select="issue"/>):
          <xsl:value-of select="elocation-id"/>.
            doi:<xsl:value-of select="article-id[@pub-id-type='doi']"/>
        </p>
        <!-- editors -->
        <xsl:for-each-group select="//contrib-group/contrib[@contrib-type='editor']" group-by="role">
 	      <xsl:call-template name="editors-list">
 	  	    <xsl:with-param name="r" select="//contrib-group/contrib[@contrib-type='editor' and role=current-grouping-key()]"/>
 	  	  </xsl:call-template>
 	    </xsl:for-each-group>
 	    <xsl:call-template name="editors-list">
 	  	  <xsl:with-param name="r" select="//contrib-group/contrib[@contrib-type='editor' and not(role)]"/>
 	    </xsl:call-template>
        <!-- history/date, pub-date -->
        <p>
          <xsl:if test="history/date[@date-type='received']">
            <strong>Received:</strong> <xsl:text> </xsl:text>
            <xsl:apply-templates select="history/date[@date-type='received']/month" mode="map"/>
            <xsl:text> </xsl:text>
            <xsl:value-of select="history/date[@date-type='received']/day"/><xsl:text>, </xsl:text>
            <xsl:value-of select="history/date[@date-type='received']/year"/><xsl:text>; </xsl:text>
          </xsl:if>
          <xsl:if test="history/date[@date-type='accepted']">
            <strong>Accepted:</strong> <xsl:text> </xsl:text>
            <xsl:apply-templates select="history/date[@date-type='accepted']/month" mode="map"/>
            <xsl:text> </xsl:text>
            <xsl:value-of select="history/date[@date-type='accepted']/day"/><xsl:text>, </xsl:text>
            <xsl:value-of select="history/date[@date-type='accepted']/year"/><xsl:text>; </xsl:text>
          </xsl:if>
          <strong>Published:</strong> <xsl:text> </xsl:text>
          <xsl:apply-templates select="pub-date[@pub-type='epub']/month" mode="map"/>
          <xsl:text> </xsl:text>
          <xsl:if test="pub-date[@pub-type='epub']/day">
            <xsl:value-of select="pub-date[@pub-type='epub']/day"/><xsl:text>, </xsl:text>
          </xsl:if>
          <xsl:value-of select="pub-date[@pub-type='epub']/year"/>
        </p>
        <!-- copyright -->
        <p>
          <xsl:choose>
            <xsl:when test="permissions/license/license-p[contains(., 'Public Domain') or contains(., 'public domain')]">
              <xsl:apply-templates select="permissions/license" mode="metadata" />
            </xsl:when>
            <xsl:otherwise>
              <strong>Copyright:</strong><xsl:text> &#169; </xsl:text>
              <xsl:apply-templates select="permissions/copyright-year" /><xsl:text> </xsl:text>
              <xsl:apply-templates select="permissions/copyright-holder" mode="metadata" /><xsl:text>. </xsl:text>
              <xsl:apply-templates select="permissions/license" mode="metadata" />
            </xsl:otherwise>
          </xsl:choose>
        </p>
        <!-- funding statement -->
        <xsl:if test="funding-group">
          <p>
            <xsl:apply-templates select="funding-group/funding-statement" mode="metadata" />
          </p>
        </xsl:if>
        <!-- competing interests -->
        <xsl:if test="author-notes/fn[@fn-type='conflict']">
          <p><strong>Competing interests:</strong><xsl:text> </xsl:text>
            <xsl:apply-templates select="author-notes/fn[@fn-type='conflict']" />
          </p>
        </xsl:if>
        <!-- glossary (abbreviations) -->
        <xsl:if test="../../back/glossary">
          <p>
            <strong><xsl:value-of select="../..//back/glossary/title"/>: </strong>
            <xsl:for-each select="../../back/glossary/def-list/def-item">
              <xsl:apply-templates select="term"/>, <xsl:apply-templates select="def "/><xsl:if test="position() != last()">; </xsl:if>
            </xsl:for-each>
          </p>
        </xsl:if>
        <!-- end of article-meta; return to previous context -->
      </xsl:for-each>
      <!-- display fn-group fn-type="other" at bottom of citation -->
      <xsl:for-each select="//back/fn-group/fn[@fn-type='other']/node()">
        <p><xsl:apply-templates/></p>
      </xsl:for-each>
      <!--Fix for FEND-886-->
      <xsl:for-each select="//front/article-meta/author-notes/fn[@fn-type='other']/node()">
        <p><xsl:apply-templates/></p>
      </xsl:for-each>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates editors summary) -->
    <xsl:template name="make-editors-summary">
      <xsl:for-each select="front/article-meta/abstract[@abstract-type='editor']">
        <div class="editorsAbstract">
          <xsl:call-template name="abstract-title"/>
          <xsl:apply-templates select="*[not(self::title)]"/>
        </div>
      </xsl:for-each>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (replaces for-each select="body" section in nlm make-article) -->
    <xsl:template name="make-body">
      <xsl:for-each select="body">
        <xsl:call-template name="newline1"/>
        <xsl:call-template name="newline1"/>
        <xsl:apply-templates/>
        <xsl:call-template name="newline1"/>
      </xsl:for-each>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="footer-metadata" />

    <!-- ============================================================= -->
    <!--  METADATA PROCESSING                                          -->
    <!-- ============================================================= -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="journal-id" mode="metadata" />
    <xsl:template match="journal-title-group" mode="metadata" />
    <xsl:template match="issn" mode="metadata" />
    <xsl:template match="isbn" mode="metadata" />
    <xsl:template match="publisher" mode="metadata" />
    <xsl:template match="publisher-name" mode="metadata-inline" />
    <xsl:template match="publisher-loc" mode="metadata-inline" />
    <xsl:template match="notes" mode="metadata" />
    <xsl:template match="journal-title" mode="metadata" />
    <xsl:template match="journal-subtitle" mode="metadata" />
    <xsl:template match="trans-title-group" mode="metadata" />
    <xsl:template match="abbrev-journal-title" mode="metadata" />
    <xsl:template match="trans-title" mode="metadata" />
    <xsl:template match="trans-subtitle" mode="metadata" />
    <xsl:template match="ext-link" mode="metadata" />
    <xsl:template match="email" mode="metadata" />
    <xsl:template match="uri" mode="metadata" />
    <xsl:template match="self-uri" mode="metadata" />
    <xsl:template match="product" mode="metadata" />
    <xsl:template match="permissions" mode="metadata" />
    <xsl:template match="copyright-statement" mode="metadata"/>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="license" mode="metadata">
      <xsl:apply-templates mode="metadata" />
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="license-p" mode="metadata">
      <xsl:apply-templates />
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="history/date" mode="metadata" />
    <xsl:template match="pub-date" mode="metadata" />
    <xsl:template name="volume-info" />
    <xsl:template match="volume | issue" mode="metadata-inline" />
    <xsl:template match="volume-id | issue-id" mode="metadata-inline" />
    <xsl:template match="volume-series" mode="metadata-inline" />
    <xsl:template match="volume" mode="metadata" />
    <xsl:template match="volume-id" mode="metadata" />
    <xsl:template match="volume-series" mode="metadata" />
    <xsl:template name="issue-info" />
    <xsl:template match="issue-title" mode="metadata-inline" />
    <xsl:template match="issue" mode="metadata" />
    <xsl:template match="issue-id" mode="metadata" />
    <xsl:template match="issue-title" mode="metadata" />
    <xsl:template match="issue-sponsor" mode="metadata" />
    <xsl:template match="issue-part" mode="metadata" />
    <xsl:template name="page-info" />
    <xsl:template match="elocation-id" mode="metadata" />
    <xsl:template match="supplement" mode="metadata" />
    <xsl:template match="related-article | related-object" mode="metadata" />
    <xsl:template match="conference" mode="metadata" />
    <xsl:template match="conf-date" mode="metadata" />
    <xsl:template match="conf-name" mode="metadata" />
    <xsl:template match="conf-acronym" mode="metadata" />
    <xsl:template match="conf-num" mode="metadata" />
    <xsl:template match="conf-loc" mode="metadata" />
    <xsl:template match="conf-sponsor" mode="metadata" />
    <xsl:template match="conf-theme" mode="metadata" />
    <xsl:template match="conf-name | conf-acronym" mode="metadata-inline" />
    <xsl:template match="conf-num" mode="metadata-inline" />
    <xsl:template match="conf-date | conf-loc" mode="metadata-inline" />
    <xsl:template match="article-id" mode="metadata" />
    <xsl:template match="award-group" mode="metadata" />
    <xsl:template match="funding-source" mode="metadata" />
    <xsl:template match="award-id" mode="metadata" />
    <xsl:template match="principal-award-recipient" mode="metadata" />
    <xsl:template match="principal-investigator" mode="metadata" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="funding-statement" mode="metadata">
      <strong>Funding: </strong>
      <xsl:apply-templates />
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="open-access" mode="metadata" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="title-group" mode="metadata">
      <xsl:apply-templates select="subtitle" mode="metadata"/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use (article title comes from ambra) -->
    <xsl:template match="title-group/article-title" mode="metadata" />

    <!-- 1/4/12: plos-specific template (pushes article-title children, enables display of italics in citation) -->
    <xsl:template match="title-group/article-title" mode="metadata-citation">
      <xsl:apply-templates />
    </xsl:template>

    <!-- 1/4/12: plos-specific template (part 1: fixes stray spaces in article citation, accounting for mixed element content) -->
    <xsl:template match="title-group/article-title/node()[last()][self::text()]" mode="metadata-citation">
      <xsl:variable name="x" select="normalize-space(concat(.,'x'))"/>
      <xsl:value-of select="substring(normalize-space(concat('x',.)),2)"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (part 2: fixes stray spaces in article citation, accounting for mixed element content) -->
    <!-- 1/4/12: added priority to disambiguate from "title-group/article-title" above -->
    <xsl:template match="title-group/article-title[not(*)]" mode="metadata-citation" priority="1">
      <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="title-group/subtitle" mode="metadata">
      <h2>
        <xsl:apply-templates/>
      </h2>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="title-group/trans-title-group" mode="metadata" />
    <xsl:template match="trans-title-group/trans-title" mode="metadata" />
    <xsl:template match="title-group/alt-title" mode="metadata" />
    <xsl:template match="title-group/fn-group" mode="metadata" />
    <xsl:template mode="metadata" match="contrib-group" />
    <xsl:template name="contrib-identify" />
    <xsl:template match="anonymous" mode="metadata" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="collab" mode="metadata">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (suppresses group author contributor names in author byline) -->
    <xsl:template match="collab/contrib-group"/>

    <!-- 1/4/12: plos modifications (formats names in author byline) -->
    <xsl:template match="contrib/name" mode="metadata">
      <xsl:call-template name="write-name"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates first names in author byline) -->
    <xsl:template match="given-names" mode="contrib-abbr">
      <xsl:call-template name="abbreviate-name">
        <xsl:with-param name="n" select="."/>
      </xsl:call-template>
      <xsl:text> </xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates period after initial in given-name in author byline) -->
    <xsl:template name="abbreviate-name">
      <xsl:param name="n"/>
      <xsl:variable name="x" select="normalize-space($n)"/>
      <xsl:value-of select="$x"/>
      <xsl:if test="substring($x,string-length($x),1) != '.' and (string-length($x) = 1
           or (string-length($x) > 1 and substring($x,string-length($x)-1,1)=' '))">
        <xsl:text>.</xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (adds xref symbols to author byline) -->
    <xsl:template match="name" mode="metadata-inline">
      <xsl:apply-templates select="../xref[@ref-type='aff']" mode="metadata-inline"/>
      <xsl:if test="../@equal-contrib='yes'">
        <sup><a href="#equal-contrib">#</a></sup>
      </xsl:if>
      <xsl:apply-templates select="../xref[@ref-type='fn']" mode="metadata-inline"/>
      <!-- if the deceased attribute is set and there isn't already a deceased footnote, output a dagger -->
      <xsl:if test="../@deceased='yes' and not(../xref/sup='‡') and not(../ref/sup='&amp;dagger;') and not(../ref/sup='&amp;Dagger;')">
        <sup><a href="#deceased">&#x2020;</a></sup>
      </xsl:if>
      <xsl:apply-templates select="../xref[@ref-type='corresp']" mode="metadata-inline"/>
      <xsl:apply-templates select="../xref[@ref-type='author-notes']" mode="metadata-inline"/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="contrib-amend" />
    <xsl:template match="degrees" mode="metadata-inline" />
    <xsl:template match="xref" mode="metadata-inline" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="xref[@ref-type='author-notes']" mode="metadata-inline">
      <xsl:choose>
        <xsl:when test="not(.//italic) and not (.//sup)">
          <sup><em>
            <xsl:element name="a">
              <xsl:attribute name="href">#<xsl:value-of select="@rid"/></xsl:attribute>
              <xsl:apply-templates/>
            </xsl:element>
          </em></sup>
        </xsl:when>
        <xsl:when test="not(.//italic)">
          <em>
            <xsl:element name="a">
              <xsl:attribute name="href">#<xsl:value-of select="@rid"/></xsl:attribute>
              <xsl:attribute name="class">fnoteref</xsl:attribute>
              <xsl:value-of select="sup"/>
            </xsl:element>
          </em>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="xref[@ref-type='corresp']" mode="metadata-inline">
      <xsl:if test="./sup">
        <sup>
          <xsl:element name="a">
            <xsl:attribute name="href">#<xsl:value-of select="@rid"/></xsl:attribute>
            <xsl:attribute name="class">fnoteref</xsl:attribute>
            <xsl:value-of select="sup"/>
          </xsl:element>
        </sup>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="xref[@ref-type='aff']" mode="metadata-inline">
      <xsl:if test="./sup">
        <sup>
          <xsl:element name="a">
            <xsl:attribute name="href">#<xsl:value-of select="@rid"/></xsl:attribute>
            <xsl:value-of select="sup"/>
          </xsl:element>
        </sup>
      </xsl:if>
      <xsl:if test="following-sibling::xref[@ref-type='aff']"><sup>,</sup></xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="xref[@ref-type='fn']" mode="metadata-inline">
      <xsl:if test="./sup">
        <sup>
          <xsl:element name="a">
            <xsl:attribute name="href">#<xsl:value-of select="@rid"/></xsl:attribute>
            <xsl:value-of select="sup"/>
          </xsl:element>
        </sup>
      </xsl:if>
      <xsl:if test="following-sibling::xref[@ref-type='fn']"><sup>,</sup></xsl:if>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="contrib-info" />
    <xsl:template mode="metadata" match="address[not(addr-line) or not(*[2])]" />
    <xsl:template match="address" mode="metadata" />
    <xsl:template mode="metadata" priority="2" match="address/*" />

    <!-- 1/4/12: plos-specific template (part 1: fixes stray spaces in addr-line after enabling display of italics and other formatting, accounting for mixed element content) -->
    <xsl:template match="addr-line/node()[last()][self::text()]">
      <xsl:variable name="x" select="normalize-space(concat(.,'x'))"/>
      <xsl:value-of select="substring(normalize-space(concat('x',.)),2)"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (part 2: fixes stray spaces in addr-line after enabling display of italics and other formatting, accounting for mixed element content) -->
    <xsl:template match="addr-line[not(*)]">
      <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="aff" mode="metadata"/>

    <!-- 1/4/12: plos-specific template (creates editor list in citation) -->
    <xsl:template name="editors-list">
      <xsl:param name="r"/>
      <p>
        <xsl:for-each select="$r">
          <!-- for the first item, print out the role first, i.e. Editor -->
          <xsl:if test="position()=1">
            <strong>
              <xsl:choose>
                <xsl:when test="role">
                  <xsl:value-of select="role"/>
                </xsl:when>
                <xsl:otherwise>
                  Academic Editor
                </xsl:otherwise>
              </xsl:choose>
              <!-- if multiple editors, make role plural -->
              <xsl:if test="last() > 1">s</xsl:if>
              <xsl:text>: </xsl:text>
            </strong>
          </xsl:if>
          <xsl:apply-templates select="name | collab" mode="metadata"/>
          <xsl:apply-templates select="*[not(self::name) and not(self::collab) and not(self::xref)
                and not(self::degrees) and not(self::role)]" mode="metadata"/>
          <xsl:variable name="matchto" select="xref/@rid"/>
          <xsl:if test="../following-sibling::aff">
            <!-- use commas between name & aff if single editor; else use parens -->
            <xsl:choose>
              <xsl:when test="position() = 1 and position() = last()">
                <xsl:text>, </xsl:text>
                <xsl:apply-templates select="../following-sibling::aff[@id=$matchto]" mode="editor-metadata"/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text> (</xsl:text>
                <xsl:apply-templates select="../following-sibling::aff[@id=$matchto]" mode="editor-metadata"/>
                <xsl:text>)</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:if>
          <!-- appropriately place commas and "and" -->
          <xsl:if test="position() != last()">
            <xsl:text>, </xsl:text>
          </xsl:if>
          <xsl:if test="position() = last()-1">
            <xsl:text>and </xsl:text>
          </xsl:if>
        </xsl:for-each>
      </p>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="aff" mode="editor-metadata">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates author initials in citation) -->
    <xsl:template name="makeInitials">
      <xsl:param name="x" />
      <xsl:for-each select="tokenize($x,'\s+')">
        <xsl:choose>
          <xsl:when test="contains(.,'-')">
            <xsl:for-each select="tokenize(.,'-')">
              <xsl:value-of select="substring(.,1,1)"/>
              <xsl:if test="position()!=last()">-</xsl:if>
            </xsl:for-each>
          </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="substring(.,1,1)"/>
        </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="author-comment" mode="metadata" />
    <xsl:template match="bio" mode="metadata" />

    <!-- 1/4/12: plos modifications  -->
    <xsl:template match="on-behalf-of" mode="metadata">
      <xsl:if test="not(../following-sibling::contrib)">
        <xsl:text>, </xsl:text>
      </xsl:if>
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="role" mode="metadata" />
    <xsl:template match="author-notes" mode="metadata" />

    <!-- 1/4/12: plos modifications (creates corresponding author footnote) -->
    <xsl:template match="author-notes/corresp" mode="metadata">
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use. removed author-notes/fn from list, we process independently -->
    <xsl:template match="author-notes/p" mode="metadata" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="author-notes/fn[@fn-type='current-aff']" mode="metadata">
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="author-notes/fn[@fn-type='deceased']" mode="metadata">
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="author-notes/fn[@fn-type='other']" mode="metadata">
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="supplementary-material" mode="metadata" />
    <xsl:template match="article-categories" mode="metadata" />
    <xsl:template match="article-categories/subj-group" mode="metadata" />
    <xsl:template match="subj-group" mode="metadata" />
    <xsl:template match="subj-group/subj-group" mode="metadata" />
    <xsl:template match="subj-group/subject" mode="metadata" />
    <xsl:template match="series-title" mode="metadata" />
    <xsl:template match="series-text" mode="metadata" />
    <xsl:template match="kwd-group" mode="metadata" />
    <xsl:template match="title" mode="metadata" />
    <xsl:template match="kwd" mode="metadata" />
    <xsl:template match="compound-kwd" mode="metadata" />
    <xsl:template match="compound-kwd-part" mode="metadata" />
    <xsl:template match="counts" mode="metadata" />
    <xsl:template mode="metadata" match="fig-count | table-count | equation-count | ref-count | page-count | word-count" />
    <xsl:template match="fig-count" mode="metadata-label" /> <!-- nlm says table-count, must be wrong b/c duplicated below -->
    <xsl:template match="table-count" mode="metadata-label" />
    <xsl:template match="equation-count" mode="metadata-label" />
    <xsl:template match="ref-count" mode="metadata-label" />
    <xsl:template match="page-count" mode="metadata-label" />
    <xsl:template match="word-count" mode="metadata-label" />
    <xsl:template mode="metadata" match="custom-meta-group" />
    <xsl:template match="custom-meta" mode="metadata" />
    <xsl:template match="meta-name | meta-value" mode="metadata-inline" />

    <!-- ============================================================= -->
    <!--  REGULAR (DEFAULT) MODE                                       -->
    <!-- ============================================================= -->

    <!-- 1/4/12: plos-specific template (creates section numbering in body) -->
    <xsl:template name="make-section-id">
      <xsl:attribute name="id">
        <xsl:value-of select="concat('section',count(preceding-sibling::sec)+1)"/>
      </xsl:attribute>
    </xsl:template>

    <xsl:template name="make-section-class">
      <xsl:attribute name="class">section</xsl:attribute>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="body/sec">
      <xsl:call-template name="newline1"/>
      <div>
        <xsl:call-template name="make-section-id"/>
        <xsl:call-template name="make-section-class"/>
        <xsl:if test="descendant::title[1] != ''">
          <xsl:element name="a">
            <xsl:attribute name="id"><xsl:value-of select="@id" /></xsl:attribute>
            <xsl:attribute name="name"><xsl:value-of select="@id" /></xsl:attribute>
            <xsl:attribute name="toc"><xsl:value-of select="@id" /></xsl:attribute>
            <xsl:attribute name="title"><xsl:value-of select="descendant::title[1]" /></xsl:attribute>
          </xsl:element>
        </xsl:if>
        <xsl:apply-templates/>
      </div>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="sec">
      <xsl:apply-templates/>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="*" mode="drop-title" />
    <xsl:template match="title | sec-meta" mode="drop-title" />
    <xsl:template match="app" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="ref-list" name="ref-list">
      <div>
        <xsl:choose>
          <xsl:when test="not(title)">
            <a id="refs" name="refs" toc="refs" title="References"/>
            <h3>References</h3>
            <xsl:call-template name="newline1"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="title"/>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates select="p"/>
        <ol class="references">
          <xsl:for-each select="ref">
            <xsl:sort data-type="number" select="label"/>
            <li>
              <span class="label">
                <xsl:value-of select="label"/>.
              </span>
              <a>
                <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
                <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
              </a>
              <xsl:variable name="cit" select="element-citation | mixed-citation | nlm-citation"/>
              <xsl:apply-templates select="$cit"/>
              <xsl:text> </xsl:text>
              <xsl:if test="$cit[@publication-type='journal']">
                <xsl:variable name="apos">'</xsl:variable>
                <xsl:if test="$cit/extraCitationInfo">
                  <xsl:if test="not(element-citation//ext-link | mixed-citation//ext-link | nlm-citation//ext-link)">
                    <xsl:element name="ul">
                      <xsl:attribute name="class">find</xsl:attribute>
                      <xsl:attribute name="data-citedArticleID"><xsl:value-of select="$cit/extraCitationInfo/@citedArticleID"/></xsl:attribute>
                      <xsl:if test="$cit/extraCitationInfo/@doi">
                        <xsl:attribute name="data-doi"><xsl:value-of select="$cit/extraCitationInfo/@doi"/></xsl:attribute>
                      </xsl:if>
                      <xsl:if test="$cit/extraCitationInfo/@crossRefUrl">
                        <xsl:element name="li">
                          <xsl:element name="a">
                            <xsl:attribute name="href"><xsl:value-of select="$cit/extraCitationInfo/@crossRefUrl"/></xsl:attribute>
                            <xsl:attribute name="onclick">window.open(this.href, 'ambraFindArticle', ''); return false;</xsl:attribute>
                            <xsl:attribute name="title">Go to article in CrossRef</xsl:attribute>
                            CrossRef
                          </xsl:element>
                        </xsl:element>
                      </xsl:if>
                      <xsl:if test="$cit/extraCitationInfo/@pubMedUrl">
                        <xsl:element name="li">
                          <xsl:element name="a">
                            <xsl:attribute name="href"><xsl:value-of select="$cit/extraCitationInfo/@pubMedUrl"/></xsl:attribute>
                            <xsl:attribute name="onclick">window.open(this.href, 'ambraFindArticle', ''); return false;</xsl:attribute>
                            <xsl:attribute name="title">Go to article in PubMed</xsl:attribute>
                            PubMed/NCBI
                          </xsl:element>
                        </xsl:element>
                      </xsl:if>
                      <xsl:if test="$cit/extraCitationInfo/@googleScholarUrl">
                        <xsl:element name="li">
                          <xsl:element name="a">
                            <xsl:attribute name="href"><xsl:value-of select="$cit/extraCitationInfo/@googleScholarUrl"/></xsl:attribute>
                            <xsl:attribute name="onclick">window.open(this.href, 'ambraFindArticle', ''); return false;</xsl:attribute>
                            <xsl:attribute name="title">Go to article in Google Scholar</xsl:attribute>
                            Google Scholar
                          </xsl:element>
                        </xsl:element>
                      </xsl:if>
                    </xsl:element>
                  </xsl:if>
                  <xsl:if test="element-citation//ext-link | mixed-citation//ext-link | nlm-citation//ext-link">
                    <xsl:element name="ul">
                      <xsl:attribute name="class">find-nolinks</xsl:attribute>
                    </xsl:element>
                  </xsl:if>
                </xsl:if>
                <xsl:if test="not($cit/extraCitationInfo)">
                  <xsl:element name="ul">
                    <xsl:attribute name="class">find-nolinks</xsl:attribute>
                  </xsl:element>
                </xsl:if>
              </xsl:if>
              <xsl:if test="$cit[@publication-type!='journal']">
                <xsl:element name="ul">
                  <xsl:attribute name="class">find-nolinks</xsl:attribute>
                </xsl:element>
              </xsl:if>
            </li>
          </xsl:for-each>
        </ol>
      </div>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="sec-meta" />
    <xsl:template match="sec-meta/contrib-group" />
    <xsl:template match="sec-meta/kwd-group" />

    <!-- ============================================================= -->
    <!--  Titles                                                       -->
    <!-- ============================================================= -->

    <!-- 1/4/12: MAIN TITLE TEMPLATES  -->

    <!-- 1/4/12: suppress, we don't use. removed abstract/title, body/*/title, back[not(title)]/*/title from list (we process independently) -->
    <xsl:template name="main-title" match="back/title" />

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="abstract/title">
      <xsl:call-template name="newline1"/>
      <h2>
        <xsl:apply-templates/>
      </h2>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates main level section headings) -->
    <xsl:template match="body/sec/title">
      <!-- only output an h3 if the body/sec/title has content -->
      <xsl:if test="string(.)">
        <h3>
          <xsl:apply-templates/>
        </h3>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: SECTION TITLE TEMPLATES -->

    <!-- 1/4/12: suppress, we don't use. removed abstract/sec/title, body/*/*/title, back[not(title)]/*/*/title from list (we process independently) -->
    <xsl:template name="section-title" match="back[title]/*/title" />

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="abstract/sec/title">
      <xsl:call-template name="newline1"/>
      <!-- only output an h3 if the abstract title has content -->
      <xsl:if test="string-length() &gt; 0">
        <h3>
          <xsl:apply-templates/>
        </h3>
      </xsl:if>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template name="abstract-title">
      <xsl:variable name="idx" select="count(preceding-sibling::abstract)"/>
      <xsl:variable name="abs_id">abstract<xsl:value-of select="$idx"/></xsl:variable>
      <xsl:choose>
        <!-- if there's a title, use it -->
        <xsl:when test="title">
          <xsl:element name="a">
            <xsl:attribute name="id"><xsl:value-of select="$abs_id"/></xsl:attribute>
            <xsl:attribute name="name"><xsl:value-of select="$abs_id"/></xsl:attribute>
            <xsl:attribute name="toc"><xsl:value-of select="$abs_id"/></xsl:attribute>
            <xsl:attribute name="title"><xsl:value-of select="title"/></xsl:attribute>
          </xsl:element>
        <xsl:apply-templates select="title"/>
        </xsl:when>
        <!-- if there's no title, create one -->
        <xsl:when test="self::abstract">
          <xsl:element name="a">
            <xsl:attribute name="id"><xsl:value-of select="$abs_id"/></xsl:attribute>
            <xsl:attribute name="name"><xsl:value-of select="$abs_id"/></xsl:attribute>
            <xsl:attribute name="toc"><xsl:value-of select="$abs_id"/></xsl:attribute>
            <xsl:attribute name="title">Abstract</xsl:attribute>
          </xsl:element>
          <h2><xsl:text>Abstract</xsl:text></h2>
        </xsl:when>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates article second-level heading) -->
    <xsl:template match="body/sec/sec/title">
      <xsl:call-template name="newline1"/>
      <h4>
        <xsl:apply-templates/>
      </h4>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: SUBSECTION TITLES -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="subsection-title" match="abstract/*/*/title | back[title]/*/*/title | back[not(title)]/*/*/*/title" />

    <!-- 1/4/12: plos-specific template (creates article third-level heading) -->
    <xsl:template match="body/sec/sec/sec/title">
      <h5>
        <xsl:apply-templates/>
        <xsl:call-template name="punctuation" />
      </h5>
    </xsl:template>

    <!-- 1/4/12: BLOCK AND MISC TITLES -->

    <!-- 1/4/12: suppress, we don't use. removed boxed-text/title from list (we process independently) -->
    <xsl:template name="block-title" priority="2" match="list/title | def-list/title | boxed-text/title | verse-group/title | glossary/title | kwd-group/title" />

    <!-- 1/12/12: plos-specific template -->
    <xsl:template match="ack/sec/title">
      <xsl:call-template name="newline1"/>
      <h4>
        <xsl:apply-templates/>
      </h4>
      <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="ref-list[not(ancestor::back)]/title">
      <a>
        <xsl:attribute name="id"><xsl:value-of select="replace(lower-case(.),' ','')"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="replace(lower-case(.),' ','')"/></xsl:attribute>
      </a>
      <h3>
        <xsl:apply-templates/>
      </h3>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="back/ref-list/title">
      <a>
        <xsl:attribute name="id"><xsl:value-of select="replace(lower-case(.),' ','')"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="replace(lower-case(.),' ','')"/></xsl:attribute>
        <xsl:attribute name="toc"><xsl:value-of select="replace(lower-case(.),' ','')"/></xsl:attribute>
        <xsl:attribute name="title">
          <xsl:choose>
            <xsl:when test="string-length(.) &gt; 0">
              <xsl:value-of select="."/>
            </xsl:when>
            <xsl:otherwise>
              References
            </xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </a>
      <h3>
        <xsl:apply-templates/>
      </h3>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="notes/sec/title">
      <h3><xsl:value-of select="."/></h3>
    </xsl:template>

    <!-- 1/4/12: plos modifications (creates any other titles not already specified) -->
    <xsl:template match="title">
      <xsl:choose>
        <!-- if there's a title, use it -->
        <xsl:when test="count(ancestor::sec) > 1">
          <xsl:call-template name="newline1"/>
          <h4>
            <xsl:apply-templates/>
          </h4>
          <xsl:call-template name="newline1"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="newline1"/>
          <h3>
            <xsl:apply-templates/>
          </h3>
          <xsl:call-template name="newline1"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="subtitle" />

    <!-- ============================================================= -->
    <!--  Figures, lists and block-level objects                       -->
    <!-- ============================================================= -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="address" />
    <xsl:template name="address-line" />
    <xsl:template match="address/*" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="alternatives">
      <xsl:apply-templates select="graphic"/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="array | disp-formula-group | fig-group | fn-group | license | long-desc | open-access | sig-block | table-wrap-foot | table-wrap-group" />
    <xsl:template match="attrib" />

    <!-- 1/4/12: suppress, we don't use (removed fig, table-wrap, and boxed-text here, process them independently) -->
    <xsl:template match="chem-struct-wrap" />

    <!-- 1/4/12: plos-specific template (creates box for figs/tables within article body, creates slideshow window) -->
    <xsl:template match="fig | table-wrap">
      <xsl:variable name="figId"><xsl:value-of select="@id"/></xsl:variable>
      <xsl:variable name="apos">'</xsl:variable>
      <xsl:if test=".//graphic">
        <xsl:variable name="imageURI"><xsl:value-of select=".//graphic/@xlink:href"/></xsl:variable>
        <xsl:variable name="slideshowURL">
          <xsl:value-of select="concat($pubAppContext, '/article/fetchObject.action?uri=',
                  $imageURI,'&amp;representation=PNG_M')"/>
        </xsl:variable>

        <xsl:variable name="pptURL">
          <xsl:value-of select="concat('/article/',$imageURI, '/powerpoint')"/>
        </xsl:variable>

        <xsl:variable name="bigImgURL">
          <xsl:value-of select="concat('/article/',$imageURI,'/largerimage')"/>
        </xsl:variable>
        <xsl:variable name="bigImgDOI">
          <xsl:value-of select="concat($imageURI,'.PNG_L')"/>
        </xsl:variable>

        <xsl:variable name="origImgURL">
          <xsl:value-of select="concat('/article/',$imageURI,'/originalimage')"/>
        </xsl:variable>
        <xsl:variable name="origImgDOI">
          <xsl:value-of select="concat($imageURI,'.TIF')"/>
        </xsl:variable>

        <xsl:variable name="targetURI">
          <xsl:value-of select="substring($imageURI, 1, (string-length($imageURI)-5))"/>
        </xsl:variable>

        <div class="figure">
          <!--id needs to be attached to "figure" div for proper anchor linking-->
          <xsl:attribute name="id"><xsl:value-of select="translate($figId, '.', '-')"/> </xsl:attribute>
          <div class="img">
            <xsl:element name="a">
              <!-- 6/13/12: added translate so names and ids have dash (for figure enhancement) -->
              <xsl:attribute name="name"><xsl:value-of select="translate($figId, '.', '-')"/></xsl:attribute>
                <xsl:attribute name="title">Click for larger image </xsl:attribute>
                <xsl:attribute name="href"><xsl:value-of select="$slideshowURL"/></xsl:attribute>
                <xsl:attribute name="data-doi"><xsl:value-of select="$targetURI"/></xsl:attribute>
                <xsl:attribute name="data-uri"><xsl:value-of select="$imageURI"/></xsl:attribute>
                <xsl:element name="img">
                  <xsl:attribute name="src">
                  <xsl:value-of select="concat($pubAppContext,'/article/fetchObject.action?uri=',$imageURI,'&amp;representation=PNG_I')"/>
                  </xsl:attribute>
                  <xsl:attribute name="alt">thumbnail</xsl:attribute>
                  <xsl:attribute name="class">thumbnail</xsl:attribute>
                </xsl:element>
              </xsl:element>
            </div>
          <!--start figure download-->
          <div class="figure-inline-download">
            Download:
            <ul>
              <li>
                <div class="icon">
                  <xsl:element name="a">
                    <xsl:attribute name="href">
                      <xsl:value-of select="$pptURL"/>
                    </xsl:attribute>
                    PPT
                  </xsl:element>
                </div>
                <xsl:element name="a">
                  <xsl:attribute name="href">
                    <xsl:value-of select="$pptURL"/>
                  </xsl:attribute>
                  PowerPoint slide
                </xsl:element>
              </li>
              <li>
                <div class="icon">
                  <xsl:element name="a">
                    <xsl:attribute name="href">
                      <xsl:value-of select="$bigImgURL"/>
                    </xsl:attribute>
                    PNG
                  </xsl:element>
                </div>
                <xsl:element name="a">
                  <xsl:attribute name="href">
                    <xsl:value-of select="$bigImgURL"/>
                  </xsl:attribute>
                  larger image
                  (<xsl:element name="span">
                    <xsl:attribute name="id">
                      <xsl:value-of select="$bigImgDOI"/>
                    </xsl:attribute>
                  </xsl:element>)
                </xsl:element>
              </li>
              <li>
                <div class="icon">
                  <xsl:element name="a">
                    <xsl:attribute name="href">
                      <xsl:value-of select="$origImgURL"/>
                    </xsl:attribute>
                    TIFF
                  </xsl:element>
                </div>
                <xsl:element name="a">
                  <xsl:attribute name="href">
                    <xsl:value-of select="$origImgURL"/>
                  </xsl:attribute>
                  original image
                  (<xsl:element name="span">
                    <xsl:attribute name="id">
                      <xsl:value-of select="$origImgDOI"/>
                    </xsl:attribute>
                  </xsl:element>)
                </xsl:element>
              </li>
            </ul>
          </div>
          <!--end figure download-->
          <p>
            <strong>
              <xsl:apply-templates select="label"/>
              <xsl:if test="caption/title">
                <xsl:text> </xsl:text>
                <span>
                  <xsl:apply-templates select="caption/title"/>
                </span>
              </xsl:if>
            </strong>
          </p>
          <xsl:apply-templates select="caption/node()[not(self::title)]"/>
          <xsl:if test="object-id[@pub-id-type='doi']">
            <span><xsl:apply-templates select="object-id[@pub-id-type='doi']"/></span>
          </xsl:if>
        </div>
      </xsl:if>
      <xsl:if test="not(.//graphic)">
        <xsl:if test=".//table">
          <div class="table-wrap">
            <xsl:attribute name="name">
              <xsl:value-of select="$figId"/>
            </xsl:attribute>
            <xsl:attribute name="id">
              <xsl:value-of select="$figId"/>
            </xsl:attribute>
            <a><xsl:attribute name="name">
              <xsl:value-of select="$figId"/>
            </xsl:attribute></a>
            <div class="expand">
              <xsl:attribute name="onclick">
                return tableOpen(<xsl:value-of select="concat($apos, $figId, $apos)"/>, "HTML");
              </xsl:attribute>
            </div>
            <div class="table">
              <xsl:apply-templates select=".//table"/>
            </div>
            <p class="caption">
              <xsl:apply-templates select="label"/>
              <xsl:if test="caption/title">
                <xsl:text> </xsl:text>
                <span>
                  <xsl:apply-templates select="caption/title"/>
                </span>
              </xsl:if>
            </p>
            <xsl:apply-templates select="caption/node()[not(self::title)]"/>
            <xsl:if test="table-wrap-foot">
              <xsl:for-each select="table-wrap-foot//fn">
                <div class="table-footnote">
                  <span class="fn-label">
                    <xsl:value-of select="label"/>
                  </span>
                  <span class="fn-text">
                    <xsl:apply-templates select="p"/>
                  </span>
                </div>
              </xsl:for-each>
            </xsl:if>
            <div class="table-download">
              <div class="icon">
                <xsl:attribute name="onclick">
                  return tableOpen(<xsl:value-of select="concat($apos, $figId, $apos)"/>, "CSV");
                </xsl:attribute>
                CSV
              </div>
              <a class="label">
                <xsl:attribute name="onclick">
                  return tableOpen(<xsl:value-of select="concat($apos, $figId, $apos)"/>, "CSV");
                </xsl:attribute>
                Download CSV
              </a>
            </div>
          </div>
        </xsl:if>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="boxed-text">
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <xsl:element name="div">
        <xsl:attribute name="class">box</xsl:attribute>
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="caption">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="caption/title">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use (removed disp-formula here, handle it separately) -->
    <xsl:template match="statement" />

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="disp-formula">
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <!-- span class='equation' goes around equations -->
      <span class="equation">
        <xsl:apply-templates select="*[not(self::label)]"/>
        <xsl:apply-templates select="label"/>
      </span>
      <br/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="glossary" />
    <xsl:template match="textual-form" />
    <xsl:template match="glossary/glossary" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="graphic | inline-graphic">
      <xsl:element name="img">
        <xsl:if test="@xlink:href">
          <xsl:variable name="graphicDOI"><xsl:value-of select="@xlink:href"/></xsl:variable>
          <xsl:attribute name="src">
            <xsl:value-of select="concat($pubAppContext,'/article/fetchObject.action?uri=',$graphicDOI,'&amp;representation=PNG')"/>
          </xsl:attribute>
        </xsl:if>
        <xsl:attribute name="class">
          <xsl:value-of>inline-graphic</xsl:value-of>
        </xsl:attribute>
      </xsl:element>
    </xsl:template>

    <!-- 1/4/12: nlm contains alt-text (suppressed here, processed within graphic|inline-graphic) -->

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="list">
      <xsl:call-template name="newline1"/>
      <xsl:choose>
        <xsl:when test="@list-type='bullet'">
          <xsl:call-template name="newline1"/>
          <ul class="bulletlist">
            <xsl:call-template name="newline1"/>
            <xsl:apply-templates/>
            <xsl:call-template name="newline1"/>
          </ul>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="newline1"/>
          <ol class="{@list-type}">
            <xsl:call-template name="newline1"/>
            <xsl:apply-templates/>
            <xsl:call-template name="newline1"/>
          </ol>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template priority="2" mode="list" match="list[@list-type='simple' or list-item/label]" />
    <xsl:template match="list[@list-type='bullet' or not(@list-type)]" mode="list" />
    <xsl:template match="list" mode="list" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="list-item">
	    <xsl:call-template name="newline1"/>
		  <li>
        <xsl:if test="../@prefix-word">
          <xsl:value-of select="../@prefix-word"/>
          <xsl:text> </xsl:text>
        </xsl:if>
		    <xsl:apply-templates/>
		  </li>
	    <xsl:call-template name="newline1"/>
	  </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="list-item/label">
      <span class="list-label">
        <xsl:apply-templates/>
        <xsl:text>. </xsl:text>
      </span>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="media" />
    <xsl:template match="license-p" /> <!-- 1/4/12: removed p from list, we process independently -->

  <!-- 1/4/12: plos modifications -->
  <!--if this changes, the two templates below, "preSiClass", and "postSiClass" have to change, too-->
  <xsl:template match="p">
    <a>
      <xsl:call-template name="makeIdNameFromXpathLocation"/>
    </a>
    <p>
      <xsl:apply-templates/>
    </p>
    <xsl:call-template name="newline1"/>
  </xsl:template>

  <!--3/1/13, add class to a specific paragraph for after styling-->
  <!--note that if 'match="p"' changes, this will have to change-->
  <xsl:template name="preSiClass">
    <a>
      <xsl:call-template name="makeIdNameFromXpathLocation"/>
    </a>
    <p class="preSiDOI">
      <xsl:apply-templates/>
    </p>
    <xsl:call-template name="newline1"/>
  </xsl:template>

  <!--3/4/13 add class to paragraphs appearing after doi in supplementary doi-->
  <!--for styling-->
  <xsl:template name="postSiClass">
    <a>
      <xsl:call-template name="makeIdNameFromXpathLocation"/>
    </a>
    <p class="postSiDOI">
      <xsl:apply-templates/>
    </p>
    <xsl:call-template name="newline1"/>
  </xsl:template>

  <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="@content-type" />

    <!-- 1/4/12: plos-specific template (overrides nlm list-item/p[not(preceding-sibling::*[not(self::label)])]) -->
    <xsl:template match="list-item/p">
      <xsl:apply-templates />
      <xsl:if test="following-sibling::p">
	    <br/>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: nlm contains list-item/p[not(preceding-sibling::*[not(self::label)])]". we override with list-item/label, can't suppress, causes p to disappear -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="product" />
    <xsl:template match="permissions" />
    <xsl:template match="copyright-statement" />
    <xsl:template match="def-list" />
    <xsl:template match="def-item" />

    <!-- 1/4/12: plos-specific template (creates def-list in the body, differs from def-list in metadata glossary) -->
    <xsl:template match="body//def-list">
      <dl>
        <xsl:for-each select="def-item">
          <dt><xsl:apply-templates select="term"/></dt>
          <dd><xsl:apply-templates select="def"/></dd>
        </xsl:for-each>
      </dl>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="def-item//p">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="def-item//named-content">
      <span class="{@content-type}">
        <xsl:apply-templates/>
      </span>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="def-item//sup | def-item//sub | def-item//em | def-item//strong">
      <xsl:element name="{local-name()}">
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="term">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="def">
       <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="disp-quote">
      <xsl:call-template name="newline1"/>
	    <blockquote>
		    <xsl:call-template name="assign-id"/>
		    <xsl:apply-templates/>
	    </blockquote>
	    <xsl:call-template name="newline1"/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="preformat">
	    <pre><xsl:call-template name="assign-id"/><xsl:apply-templates/></pre>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="ref" />
    <xsl:template match="ref/*" priority="0"/>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="mixed-citation">
      <xsl:apply-templates/>
      <xsl:if test="extraCitationInfo/@doi and not(ext-link) and not(comment/ext-link)">
        <xsl:variable name="citedArticleDoi"><xsl:value-of select="extraCitationInfo/@doi"/></xsl:variable>
        doi:
        <xsl:element name="a">
          <xsl:attribute name="href">http://dx.doi.org/<xsl:value-of select="$citedArticleDoi"/></xsl:attribute>
          <xsl:value-of select="$citedArticleDoi"/>
        </xsl:element>.
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (formats mixed-citation names, most mixed-citation formatting is in the xml) -->
    <xsl:template match="mixed-citation/name">
      <xsl:apply-templates select="surname"/>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="given-names"/>
      <xsl:if test="suffix">
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="suffix"/>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific templates for legacy references (element-citation: journal/no citation, book/other, supporting templates -->

    <!-- 6/8/12: plos-specific template: legacy nlm-citation references (need separate transform to account for different tag order) -->
    <xsl:template match="nlm-citation">
      <xsl:apply-templates select="person-group" mode="book"/>
      <xsl:apply-templates select="collab" mode="book"/>
      <xsl:apply-templates select="year" mode="none"/>
      <xsl:apply-templates select="article-title" mode="none"/>
      <xsl:apply-templates select="*[not(self::annotation) and not(self::edition) and not(self::person-group)
        and not(self::collab) and not(self::comment) and not(self::year) and not (self::article-title)]|text()" mode="none"/>
      <xsl:call-template name="citationComment"/>
      <xsl:if test="extraCitationInfo/@doi and not(ext-link) and not(comment/ext-link)">
        <xsl:variable name="citedArticleDoi"><xsl:value-of select="extraCitationInfo/@doi"/></xsl:variable>
        doi:
        <xsl:element name="a">
          <xsl:attribute name="href">http://dx.doi.org/<xsl:value-of select="$citedArticleDoi"/></xsl:attribute>
          <xsl:value-of select="$citedArticleDoi"/>
        </xsl:element>.
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template: legacy references (publication-type journal and no publication-type) -->
    <xsl:template match="element-citation">
      <xsl:apply-templates select="person-group" mode="book"/>
      <xsl:apply-templates select="collab" mode="book"/>
      <xsl:apply-templates select="*[not(self::edition) and not(self::person-group) and not(self::collab) and not(self::comment)] | text()" mode="none"/>
      <xsl:call-template name="citationComment" />
      <xsl:if test="extraCitationInfo/@doi and not(ext-link) and not(comment/ext-link)">
        <xsl:variable name="citedArticleDoi"><xsl:value-of select="extraCitationInfo/@doi"/></xsl:variable>
        doi:
        <xsl:element name="a">
          <xsl:attribute name="href">http://dx.doi.org/<xsl:value-of select="$citedArticleDoi"/></xsl:attribute>
          <xsl:value-of select="$citedArticleDoi"/>
        </xsl:element>.
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template: legacy references (publication-types book and other) -->
    <!-- 6/23/12: add nlm-citation and page-count for nlm-citation-->
    <xsl:template match="element-citation[@publication-type='book'] | element-citation[@publication-type='other'] |
                         nlm-citation[@publication-type='book'] | nlm-citation[@publication-type='other']">
     <xsl:variable name="augroupcount" select="count(person-group) + count(collab)"/>
      <xsl:choose>
        <!-- chapter in edited book -->
        <xsl:when test="$augroupcount>1 and person-group[@person-group-type!='author'] and article-title">
          <xsl:apply-templates select="person-group[@person-group-type='author']" mode="book"/>
          <xsl:apply-templates select="collab" mode="book"/>
          <xsl:apply-templates select="year | month" mode="book"/>
          <xsl:apply-templates select="article-title" mode="editedbook"/>
          <xsl:text> In:</xsl:text>
          <xsl:apply-templates select="person-group[@person-group-type='editor']" mode="book"/>
          <xsl:apply-templates select="source" mode="book"/>
          <xsl:apply-templates select="edition" mode="book"/>
          <xsl:apply-templates select="volume"  mode="book"/>
          <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
          <xsl:apply-templates select="fpage | lpage" mode="book"/>
          <xsl:apply-templates select="size | page-count" mode="book"/>
        </xsl:when>
        <!-- when person-group without pgtype exists -->
        <xsl:when test="person-group[not(@person-group-type)]">
          <xsl:apply-templates select="person-group" mode="book"/>
          <xsl:apply-templates select="collab" mode="book"/>
          <xsl:apply-templates select="year | month" mode="book"/>
          <xsl:apply-templates select="article-title" mode="book"/>
          <xsl:apply-templates select="source" mode="book"/>
          <xsl:apply-templates select="edition" mode="book"/>
          <xsl:apply-templates select="person-group[@person-group-type='editor']" mode="book"/>
          <xsl:apply-templates select="volume" mode="book"/>
          <xsl:apply-templates select="issue" mode="none"/>
          <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
          <xsl:apply-templates select="fpage | lpage" mode="book"/>
          <xsl:apply-templates select="size | page-count" mode="book"/>
        </xsl:when>
        <!-- when pgtype author exists but not chapter in edited book -->
        <xsl:when test="person-group[@person-group-type='author']">
          <xsl:apply-templates select="person-group[@person-group-type='author']" mode="book"/>
          <xsl:apply-templates select="collab" mode="book"/>
          <xsl:apply-templates select="year | month" mode="book"/>
          <xsl:apply-templates select="article-title" mode="book"/>
          <xsl:apply-templates select="source" mode="book"/>
          <xsl:apply-templates select="edition" mode="book"/>
          <xsl:apply-templates select="person-group[@person-group-type='editor']" mode="book"/>
          <xsl:apply-templates select="volume" mode="book"/>
          <xsl:apply-templates select="issue" mode="none"/>
          <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
          <xsl:apply-templates select="fpage | lpage" mode="book"/>
          <xsl:apply-templates select="size | page-count" mode="book"/>
        </xsl:when>
        <xsl:otherwise>
          <!-- all others -->
          <xsl:apply-templates select="person-group[@person-group-type='editor']"  mode="book"/>
          <xsl:apply-templates select="collab" mode="book"/>
          <xsl:apply-templates select="year | month" mode="book"/>
          <xsl:apply-templates select="article-title" mode="book"/>
          <xsl:apply-templates select="source" mode="book"/>
          <xsl:apply-templates select="edition" mode="book"/>
          <xsl:apply-templates select="volume" mode="book"/>
          <xsl:apply-templates select="issue" mode="none"/>
          <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
          <xsl:apply-templates select="fpage | lpage" mode="book"/>
          <xsl:apply-templates select="size | page-count" mode="book"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:call-template name="citationComment" />
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="year" mode="none">
      <xsl:choose>
        <xsl:when test="../month">
          <xsl:apply-templates mode="none"/>
          <xsl:text> </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text> (</xsl:text>
          <xsl:apply-templates mode="none"/>
          <xsl:text>) </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <!-- 6/8/12: comment out call-template: don't need? -->
    <xsl:template match="article-title" mode="none">
      <xsl:apply-templates/>
      <!--<xsl:call-template name="punctuation" />  -->
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="source" mode="none">
      <xsl:text> </xsl:text>
      <xsl:apply-templates/>
      <xsl:choose>
        <xsl:when test="../volume | ../fpage">
          <xsl:if test="../edition">
            <xsl:text> (</xsl:text><xsl:apply-templates select="../edition" mode="book"/><xsl:text>)</xsl:text>
          </xsl:if>
          <xsl:text> </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:if test="../edition">
            <xsl:text> (</xsl:text>
            <xsl:apply-templates select="../edition" mode="book"/>
            <xsl:text>)</xsl:text>
          </xsl:if>
          <xsl:text>. </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="volume" mode="none">
      <xsl:text> </xsl:text>
      <xsl:apply-templates/>
      <xsl:if test="not(../issue)">
        <xsl:text>: </xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="issue" mode="none">
      <xsl:if test="not(starts-with(normalize-space(),'('))">
        <xsl:text>(</xsl:text>
      </xsl:if>
      <xsl:apply-templates/>
      <xsl:if test="not(ends-with(normalize-space(),')'))">
        <xsl:text>)</xsl:text>
      </xsl:if>
      <xsl:choose>
        <xsl:when test="../fpage or ../lpage or ../elocation-id">
          <xsl:text>: </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>.</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="elocation-id" mode="none">
	    <xsl:apply-templates/>
      <xsl:text>. </xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="fpage" mode="none">
      <xsl:apply-templates/>
      <xsl:choose>
        <xsl:when test="following-sibling::lpage[1]">
          <xsl:text>&#8211;</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>.</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="lpage" mode="none">
      <xsl:apply-templates/>
      <xsl:text>.</xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="publisher-loc" mode="none">
      <xsl:apply-templates/>
      <xsl:choose>
        <xsl:when test="not(following-sibling::*)">
          <xsl:text>.</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>: </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
	  </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="publisher-name" mode="none">
      <xsl:apply-templates/>
      <xsl:text>. </xsl:text>
    </xsl:template>

    <!-- 6/8/12: plos-specific template (replicate mode book as mode none for citations without publication-type) -->
    <xsl:template match="size" mode="none">
      <xsl:apply-templates />
      <xsl:text> p.</xsl:text>
      <xsl:if test="following-sibling::*">
        <xsl:text> </xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 6/12/12: plos-specific template (replicate size but use page-count for nlm-citation) -->
    <xsl:template match="page-count" mode="none">
      <xsl:apply-templates select="@count" />
      <xsl:text> p.</xsl:text>
      <xsl:if test="following-sibling::*">
        <xsl:text> </xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="person-group" mode="book">
      <xsl:apply-templates mode="book" />
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="person-group[@person-group-type='editor']" mode="book">
      <xsl:text> </xsl:text>
      <xsl:apply-templates mode="book" />
      <xsl:choose>
        <xsl:when test="count(name) > 1">
          <xsl:text>, editors. </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>, editor. </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="name" mode="book">
      <xsl:apply-templates select="surname" />
      <xsl:text> </xsl:text>
      <xsl:if test="given-names">
        <xsl:apply-templates select="given-names" />
        <xsl:if test="suffix">
          <xsl:text> </xsl:text>
          <xsl:apply-templates select="suffix"/>
        </xsl:if>
      </xsl:if>
      <!-- punctuation after name -->
      <xsl:choose>
        <xsl:when test="../following-sibling::collab">
          <xsl:text>, </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:choose>
            <xsl:when test="position()=last()"> </xsl:when>
            <xsl:otherwise>, </xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="collab" mode="book">
	    <xsl:apply-templates/>
      <xsl:if test="following-sibling::collab">
        <xsl:text>, </xsl:text>
      </xsl:if>
	  </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="etal" mode="book">
      <xsl:text>et al.</xsl:text>
	    <xsl:choose>
		    <xsl:when test="parent::person-group/@person-group-type">
		      <xsl:choose>
		        <xsl:when test="parent::person-group/@person-group-type='author'">
			        <xsl:text> </xsl:text>
		        </xsl:when>
			      <xsl:otherwise/>
		      </xsl:choose>
		    </xsl:when>
		    <xsl:otherwise>
		      <xsl:text> </xsl:text>
		    </xsl:otherwise>
	    </xsl:choose>
	  </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="year" mode="book">
      <xsl:choose>
        <xsl:when test="../month">
          <xsl:apply-templates/>
          <xsl:text> </xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text> (</xsl:text>
          <xsl:apply-templates/>
          <xsl:text>) </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="month" mode="book">
	    <xsl:variable name="month" select="."/>
		  <xsl:choose>
		    <xsl:when test="$month='01' or $month='1' or $month='January'">Jan</xsl:when>
		    <xsl:when test="$month='02' or $month='2' or $month='February'">Feb</xsl:when>
		    <xsl:when test="$month='03' or $month='3' or $month='March'">Mar</xsl:when>
		    <xsl:when test="$month='04' or $month='4' or $month='April'">Apr</xsl:when>
		    <xsl:when test="$month='05' or $month='5' or $month='May'">May</xsl:when>
		    <xsl:when test="$month='06' or $month='6' or $month='June'">Jun</xsl:when>
		    <xsl:when test="$month='07' or $month='7' or $month='July'">Jul</xsl:when>
		    <xsl:when test="$month='08' or $month='8' or $month='August'">Aug</xsl:when>
		    <xsl:when test="$month='09' or $month='9' or $month='September'">Sep</xsl:when>
		    <xsl:when test="$month='10' or $month='October'">Oct</xsl:when>
		    <xsl:when test="$month='11' or $month='November'">Nov</xsl:when>
		    <xsl:when test="$month='12' or $month='December'">Dec</xsl:when>
		    <xsl:otherwise>
		      <xsl:value-of select="$month"/>
		    </xsl:otherwise>
		  </xsl:choose>
		  <xsl:if test="../day">
		    <xsl:text> </xsl:text>
		    <xsl:value-of select="../day"/>
		  </xsl:if>
	    <xsl:text>. </xsl:text>
	  </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="article-title" mode="book">
      <xsl:apply-templates />
      <xsl:call-template name="punctuation" />
      <xsl:text> </xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="article-title" mode="editedbook">
      <xsl:text> </xsl:text>
      <xsl:apply-templates/>
      <xsl:call-template name="punctuation" />
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="source" mode="book">
      <xsl:apply-templates/>
      <xsl:call-template name="punctuation" />
      <xsl:text> </xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="volume | edition" mode="book">
      <xsl:apply-templates/>
      <xsl:text>. </xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="fpage" mode="book">
      <xsl:if test="../lpage">
        <!-- handle old journal articles that were coded as type other, but actually had a volume, source and page numbers -->
        <xsl:choose>
          <xsl:when test="name(preceding-sibling::node()[1])='volume'">
            <xsl:text>: </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>pp. </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
        <xsl:text>&#8211;</xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="lpage" mode="book">
      <xsl:if test="../fpage">
        <xsl:apply-templates/>
        <xsl:text>.</xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="size" mode="book">
      <xsl:apply-templates />
      <xsl:text> p.</xsl:text>
      <xsl:if test="following-sibling::*">
        <xsl:text> </xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 6/23/12: plos-specific template (replicate size but use page-count for nlm-citation types book/other) -->
    <xsl:template match="page-count" mode="book">
      <xsl:apply-templates select="@count" />
      <xsl:text> p.</xsl:text>
      <xsl:if test="following-sibling::*">
        <xsl:text> </xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 6/8/12: plos-specific template -->
    <xsl:template match="comment">
      <xsl:if test="not(self::node()='.')">
        <xsl:text> </xsl:text>
        <xsl:apply-templates/>
        <xsl:if test="substring(.,string-length(.)) != '.' and not(ends-with(..,'.'))">
          <xsl:text>. </xsl:text>
        </xsl:if>
      </xsl:if>
    </xsl:template>

     <!-- 1/4/12: plos-specific template -->
    <xsl:template name="citationComment">
      <!-- only output a single comment tag that appears as the very last child of the citation -->
      <xsl:variable name="x" select="child::comment[position()=last()]"/>
      <xsl:if test="not(starts-with($x,'p.')) and not(starts-with($x,'In:') and not(starts-with($x,'pp.')))">
        <xsl:text> </xsl:text><xsl:apply-templates select="$x"/>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: end legacy reference section -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="ref/note" priority="2" />
    <xsl:template match="app/related-article | app-group/related-article | bio/related-article | body/related-article | boxed-text/related-article | disp-quote/related-article | glossary/related-article | ref-list/related-article | sec/related-article" />
    <xsl:template match="app/related-object | app-group/related-object | bio/related-object | body/related-object | boxed-text/related-object | disp-quote/related-object | glossary/related-object | ref-list/related-object | sec/related-object" />
    <xsl:template match="speech" />
    <!-- 1/4/12: speech/speaker mode speech already suppressed in nlm -->
    <xsl:template match="speech/p" mode="speech" />
    <xsl:template match="speech/speaker" />

    <!-- 1/7/13: plos modifications for figshare widget, FEND-2  -->
    <xsl:template match="supplementary-material[1]">
      <xsl:element name="div">
        <xsl:attribute name="class">figshare_widget</xsl:attribute>
        <xsl:attribute name="doi">
          <xsl:value-of select="//article/front/article-meta/article-id[@pub-id-type='doi']"/>
        </xsl:attribute>
      </xsl:element>
      <xsl:call-template name="supplementary-material" />
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="supplementary-material" name="supplementary-material">
      <xsl:variable name="the-label">
        <xsl:choose>
          <xsl:when test="label">
            <xsl:value-of select="label"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>Supplementary Material</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:element name="a">
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
      </xsl:element>
      <xsl:variable name="objURI"><xsl:value-of select="@xlink:href"/></xsl:variable>
      <p class="siTitle">
        <strong>
          <xsl:element name="a">
            <xsl:attribute name="href">
              <xsl:value-of select="concat($pubAppContext,'/article/fetchSingleRepresentation.action?uri=',$objURI)"/>
            </xsl:attribute>
            <xsl:apply-templates select="label"/>
          </xsl:element>
          <xsl:apply-templates select="caption/title"/>
        </strong>
      </p>

      <!--here, we're appending SI DOI after the caption but before the file type-->
      <xsl:variable name="siDOI">
        <xsl:value-of select="replace($objURI,'info:doi/','doi:')"/>
      </xsl:variable>

      <xsl:choose>

        <!--If one or no caption/p, insert doi-->
        <xsl:when test="count(caption/p) &lt; 2">
          <!--doi-->
          <p class="siDoi">
            <xsl:value-of select="$siDOI"/>
          </p>
          <!--add class to target styling-->
          <xsl:for-each select="caption/p">
            <xsl:call-template name="postSiClass"/>
          </xsl:for-each>
        </xsl:when>

        <!--if 2 caption/p elements, each needs it's own class for styling-->
        <xsl:when test="count(caption/p) = 2">
          <!--the first -->
          <xsl:for-each select="caption/p[position() = 1]">
            <xsl:call-template name="preSiClass"/>
          </xsl:for-each>
          <!--doi-->
          <p class="siDoi">
            <xsl:value-of select="$siDOI"/>
          </p>
          <!--the last-->
          <xsl:for-each select="caption/p[last()]">
            <xsl:call-template name="postSiClass"/>
          </xsl:for-each>
        </xsl:when>

        <!--if more than 2 caption/p elements, space out the verbal elements and close spacing between doi-->
        <!--and file type and size information-->
        <xsl:when test="count(caption/p) &gt; 2">
          <xsl:apply-templates select="caption/p[position() &lt; last() - 1]"/>
          <!--<xsl:apply-templates select="caption/p"/>-->

          <!--second from last element gets a class for styling targetting-->
          <!--<xsl:apply-templates select="caption/p[position() = last() - 1]"/>-->
          <xsl:for-each select="caption/p[position() = last() - 1]">
            <xsl:call-template name="preSiClass"/>
          </xsl:for-each>

          <!--doi goes here-->
          <p class="siDoi">
            <xsl:value-of select="$siDOI"/>
          </p>

          <!--final element-->
          <xsl:for-each select="caption/p[last()]">
            <xsl:call-template name="postSiClass"/>
          </xsl:for-each>
        </xsl:when>

      </xsl:choose>

    </xsl:template>

  <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="tex-math"/>

    <!-- 1/4/12: plos modifications (remove mml prefix from all math elements, required for MathJax to work) -->
    <xsl:template match="mml:*">
      <xsl:element name="{local-name()}">
        <xsl:copy-of copy-namespaces="no" select="@*"/>
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="verse-group" />
    <xsl:template match="verse-line" />

    <!-- 1/4/12: suppress, we don't use. (removed aff/label, we process independently) -->
    <xsl:template match="corresp/label | chem-struct/label | element-citation/label | mixed-citation/label" />

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="aff/label">
      <strong><xsl:apply-templates/></strong>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use. (removed fn, fig, supplementary-material, disp-formula, table-wrap, we process independently) -->
    <xsl:template match="app/label | boxed-text/label | chem-struct-wrap/label | ref/label | statement/label" priority="2" />

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="author-notes/fn/label">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="disp-formula//label">
      <span class="note">
        <xsl:apply-templates/>
      </span>
    </xsl:template>

    <!-- 1/4/12: plos modifications (all labels not otherwise specified) -->
    <xsl:template match="label" name="label">
      <xsl:apply-templates/>
      <xsl:text>. </xsl:text>
    </xsl:template>

    <!-- ============================================================= -->
    <!--  TABLES                                                       -->
    <!-- ============================================================= -->

    <!-- Tables are already in XHTML, and can simply be copied through -->

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="table | thead | tbody | col | colgroup | tr | th | td">
      <xsl:copy copy-namespaces="no">
        <xsl:apply-templates select="@*" mode="table-copy"/>
          <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates/>
      </xsl:copy>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="tfoot" />
    <xsl:template match="array/tbody" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="@*" mode="table-copy">
      <xsl:copy-of copy-namespaces="no" select="."/>
    </xsl:template>

    <!-- ============================================================= -->
    <!--  INLINE MISCELLANEOUS                                         -->
    <!-- ============================================================= -->
    <!--  Templates strictly for formatting follow; these are templates to handle various inline structures -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="abbrev" />
    <xsl:template match="abbrev/def" />
    <xsl:template match="p/address | license-p/address | named-content/p | styled-content/p" />
    <xsl:template match="address/*" mode="inline" />
    <xsl:template match="award-id" />
    <xsl:template match="award-id[normalize-space(@rid)]" />
    <xsl:template match="break" />

    <!-- 1/4/12: nlm contains email -->

    <!-- 1/4/12: suppress, we don't use. removed ext-link from list (we process independently) -->
    <xsl:template match="uri | inline-supplementary-material" />

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="ext-link">
      <a>
        <xsl:call-template name="assign-href"/>
        <xsl:apply-templates/>
      </a>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use  -->
    <xsl:template match="funding-source" />
    <xsl:template match="hr" />
    <xsl:template match="chem-struct" />

    <!-- 1/4/12: nlm contains inline-formula (along with chem-struct, we only suppress chem-struct portion) -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="chem-struct-wrap/chem-struct" />
    <xsl:template match="milestone-start | milestone-end" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="object-id">
      <xsl:choose>
        <xsl:when test="@pub-id-type">
          <xsl:value-of select="@pub-id-type"/>
        </xsl:when>
        <xsl:otherwise>
          <span class="gen">
            <xsl:text>Object ID</xsl:text>
          </span>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>:</xsl:text>
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="sig" />
    <xsl:template match="target" />
    <xsl:template match="styled-content" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="named-content">
      <xsl:choose>
        <xsl:when test="@xlink:href">
          <a>
            <xsl:call-template name="assign-href"/>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
          </a>
        </xsl:when>
        <xsl:otherwise>
          <span>
            <xsl:attribute name="class"><xsl:value-of select="@content-type" /></xsl:attribute>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
          </span>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="private-char" />
    <xsl:template match="glyph-data | glyph-ref" />
    <xsl:template match="related-article" />
    <xsl:template match="related-object" />
    <xsl:template match="xref[not(normalize-space())]" />

    <!-- 1/4/12: plos modifications (default if not one of the following ref-types (covers ref-type supplementary-material)) -->
    <xsl:template match="xref">
      <xsl:call-template name="assign-id"/>
      <a href="#{@rid}">
        <xsl:choose>
          <!-- if xref not empty -->
          <xsl:when test="child::node()">
            <xsl:apply-templates/>
          </xsl:when>
          <xsl:otherwise>
            <!-- if empty -->
            <xsl:value-of select="@rid"/>
          </xsl:otherwise>
        </xsl:choose>
      </a>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (superscript fn xrefs) -->
    <xsl:template match="xref[@ref-type='fn']">
      <span class="xref">
        <xsl:call-template name="assign-id"/>
        <sup>
          <!-- if immediately-preceding sibling was an xref, punctuate (otherwise assume desired punctuation is in the source) -->
          <xsl:if test="local-name(preceding-sibling::node()[1])='xref'">
            <span class="gen"><xsl:text>, </xsl:text></span>
          </xsl:if>
          <a href="#{@rid}"><xsl:apply-templates/></a>
        </sup>
      </span>
    </xsl:template>

    <!-- 1/4/12 plos-specific template (superscript table-fn xrefs) -->
    <xsl:template match="xref[@ref-type='table-fn']">
      <span class="xref">
        <xsl:call-template name="assign-id"/>
        <sup>
          <!-- if immediately-preceding sibling was an xref, punctuate (otherwise assume desired punctuation is in the source) -->
          <xsl:if test="local-name(preceding-sibling::node()[1])='xref'">
            <span class="gen"><xsl:text>, </xsl:text></span>
          </xsl:if>
          <xsl:apply-templates/>
        </sup>
      </span>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <xsl:template match="xref[@ref-type='bibr']">
      <!-- if immediately-preceding sibling was an xref, punctuate (otherwise assume desired punctuation is in the source) -->
      <xsl:if test="local-name(preceding-sibling::node()[1])='xref'">
        <xsl:text>,</xsl:text>
      </xsl:if>
      <a href="#{@rid}"><xsl:apply-templates/></a>
    </xsl:template>

    <!-- 1/4/12: plos-specific template -->
    <!-- 6/13/12: added translate so names and ids of figs have dashes (for figure enhancement) -->
    <xsl:template match="xref[@ref-type='fig'] | xref[@ref-type='table']">
      <a href="#{translate(@rid, '.', '-')}">
        <xsl:apply-templates/>
      </a>
    </xsl:template>

    <!-- 1/4/12: plos modifications (transform to <strong> instead of <b>) -->
    <xsl:template match="bold">
	    <strong>
	      <xsl:apply-templates/>
	    </strong>
	  </xsl:template>

    <!-- 1/4/12: plos modifications (transform to <em> instead of <i>) -->
	  <xsl:template match="italic">
      <em>
		    <xsl:apply-templates/>
	    </em>
	  </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="monospace">
	    <span class="monospace">
		    <xsl:apply-templates/>
	    </span>
	  </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="overline">
	    <span class="overline">
		    <xsl:apply-templates/>
	    </span>
	  </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="price" />
    <xsl:template match="roman" />
    <xsl:template match="sans-serif" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="sc">
      <span class="small-caps">
        <xsl:apply-templates/>
      </span>
	  </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="strike">
      <span class="strike">
        <xsl:apply-templates/>
      </span>
    </xsl:template>

    <!-- 1/4/12: nlm contains templates for sub and sup -->

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="underline">
      <span class="underline">
        <xsl:apply-templates/>
      </span>
	  </xsl:template>


    <!-- ============================================================= -->
    <!--  BACK MATTER                                                  -->
    <!-- ============================================================= -->

    <!-- 1/4/12: nlm contains variable loose-footnotes. we don't use -->

    <!-- 1/4/12: plos modifications (creates back section) -->
    <xsl:template name="make-back">
      <xsl:for-each select="back">
        <xsl:apply-templates select="ack"/>
        <xsl:call-template name="author-contrib"/>
        <xsl:apply-templates select="notes"/>
        <xsl:apply-templates select="*[not(self::title) and not(self::fn-group) and not(self::ack) and not(self::notes)]"/>
        <xsl:call-template name="newline1"/>
        <xsl:for-each select="//abstract[@abstract-type='patient']">
          <div class="patient">
            <a id="patient" name="patient" toc="patient" title="Patient Summary"/>
            <h3><xsl:value-of select="title"/></h3>
            <xsl:apply-templates select="*[not(self::title)]"/>
          </div>
        </xsl:for-each>
      </xsl:for-each>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates author contributions section) -->
    <xsl:template name="author-contrib">
      <xsl:if test="../front/article-meta/author-notes/fn[@fn-type='con']">
        <div class="contributions"><a id="authcontrib" name="authcontrib" toc="authcontrib"
                title="Author Contributions"/><h3>Author Contributions</h3>
          <p>
            <xsl:apply-templates select="../front/article-meta/author-notes/fn[@fn-type='con']"/>
          </p>
        </div>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="back" />
    <xsl:template name="footnotes" />

    <!-- 1/4/12: plos modifications (creates acknowledgments section) -->
    <xsl:template match="ack">
      <xsl:call-template name="newline1"/>
      <xsl:if test="position()>1">
        <hr class="section-rule"/>
      </xsl:if>
      <xsl:call-template name="newline1"/>
      <div >
        <xsl:call-template name="assign-id"/>
        <xsl:if test="not(title)">
          <a id="ack" name="ack" toc="ack" title="Acknowledgments"/><h3>Acknowledgments</h3>
          <xsl:call-template name="newline1"/>
        </xsl:if>
        <xsl:apply-templates/>
      </div>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="app-group" />
    <xsl:template match="back/bio" />
    <xsl:template match="back/fn-group" />
    <xsl:template match="back/glossary" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="back/ref-list">
      <xsl:call-template name="ref-list"/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="back/notes">
      <xsl:call-template name="newline1"/>
      <xsl:if test="position()>1">
        <hr class="section-rule"/>
      </xsl:if>
      <xsl:call-template name="newline1"/>
      <div class="notes">
        <xsl:call-template name="assign-id"/>
        <xsl:apply-templates/>
        <xsl:call-template name="newline1"/>
      </div>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="backmatter-section" />


    <!-- ============================================================= -->
    <!--  FOOTNOTES                                                    -->
    <!-- ============================================================= -->

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="fn">
      <xsl:apply-templates/>
    </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="fn-group/fn | table-wrap-foot/fn | table-wrap-foot/fn-group/fn" />
    <xsl:template match="fn" mode="footnote" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="fn/p">
      <xsl:apply-templates />
    </xsl:template>

    <!-- ============================================================= -->
    <!--  MODE 'label-text'
	      Generates label text for elements and their cross-references -->
    <!-- ============================================================= -->

    <!-- 1/4/12: nlm contains a bunch of variables, we don't use -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template mode="label" match="*" name="block-label" />
    <xsl:template mode="label" match="ref" />
    <xsl:template match="app" mode="label-text" />
    <xsl:template match="boxed-text" mode="label-text" />
    <xsl:template match="disp-formula" mode="label-text" />
    <xsl:template match="chem-struct-wrap" mode="label-text" />
    <xsl:template match="fig" mode="label-text" />
    <xsl:template match="front//fn" mode="label-text" />
    <xsl:template match="table-wrap//fn" mode="label-text" />
    <xsl:template match="fn" mode="label-text" />
    <xsl:template match="ref" mode="label-text" />
    <xsl:template match="statement" mode="label-text" />
    <xsl:template match="supplementary-material" mode="label-text" />
    <xsl:template match="table-wrap" mode="label-text" />
    <xsl:template match="*" mode="label-text" />
    <xsl:template match="label" mode="label-text" />
    <xsl:template match="text()" mode="inline-label-text" />

    <!-- ============================================================= -->
    <!--  Writing a name                                               -->
    <!-- ============================================================= -->

    <!-- Called when displaying structured names in metadata         -->

    <!-- 1/4/12: plos modifications (creates author names in metadata) -->
    <!-- 1/4/12: commented out logic for eastern/western names. edit when we implement name-style eastern -->
    <xsl:template name="write-name" match="name">
      <xsl:apply-templates select="prefix" mode="inline-name"/>
      <!-- <xsl:apply-templates select="surname[../@name-style='eastern']" mode="inline-name"/> -->
      <xsl:apply-templates select="given-names" mode="contrib-abbr"/>
      <xsl:apply-templates select="surname" mode="inline-name"/>
      <!--<xsl:apply-templates select="surname[not(../@name-style='eastern')]" mode="inline-name"/> -->
      <xsl:apply-templates select="suffix" mode="inline-name"/>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="prefix" mode="inline-name">
      <xsl:apply-templates/>
      <xsl:text> </xsl:text>
    </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <!-- 1/4/12: commented out eastern/western logic. edit when we implement name-style eastern (possibly use generic nlm) -->
    <xsl:template match="given-names" mode="inline-name">
      <xsl:apply-templates/>
      <xsl:text> </xsl:text>
      <!--<xsl:if test="../surname[not(../@name-style='eastern')] | ../suffix">
        <xsl:text> </xsl:text>
      </xsl:if>-->
    </xsl:template>

    <!-- 1/4/12: plos modifications (overrides both nlm contrib/name/surname mode inline-name and surname mode inline-name (identical in nlm)) -->
    <!-- 1/4/12: edit when we implement name-style eastern, maybe use nlm version -->
	  <xsl:template match="surname" mode="inline-name">
	    <xsl:apply-templates/>
      <!--<xsl:if test="../given-names[../@name-style='eastern'] | ../suffix">
        <xsl:text> </xsl:text>
      </xsl:if>-->
	  </xsl:template>

    <!-- 1/4/12: plos modifications -->
    <xsl:template match="suffix" mode="inline-name">
	    <xsl:text> </xsl:text>
	    <xsl:apply-templates/>
	  </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="string-name"/>

    <!-- ============================================================= -->
    <!--  UTILITY TEMPLATES                                           -->
    <!-- ============================================================= -->

  <xsl:template name="makeIdNameFromXpathLocation">
    <xsl:variable name="idFromXpath">
      <xsl:call-template name="createIdNameXpath">
        <xsl:with-param name="theNode" select="."/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:attribute name="id">
      <xsl:value-of select="substring($idFromXpath, 2)"/>
    </xsl:attribute>
    <xsl:attribute name="name">
      <xsl:value-of select="substring($idFromXpath, 2)"/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template name="createIdNameXpath">
    <xsl:param name="theNode" select="."/>
    <xsl:choose>
      <xsl:when test="$theNode[1]">
        <xsl:choose>
          <xsl:when test="not($theNode[1]/..)">
            <!-- cann't figure out when this is used -->
            <xsl:text>.</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:for-each select="$theNode[1]/ancestor-or-self::*[not(self::aml:annotated)]">
              <xsl:text/>.<xsl:value-of select="name()"/>
              <xsl:text/><xsl:value-of select="count(preceding-sibling::*[name() = name(current())]) + 1"/><xsl:text/>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="$theNode">
        <xsl:choose>
          <xsl:when test="not($theNode/..)">
            <!-- cann't figure out when this is used -->
            <xsl:text>.</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:for-each select="$theNode/ancestor-or-self::*[not(self::aml:annotated)]">
              <xsl:text/>.<xsl:value-of select="name()"/>
              <xsl:text/><xsl:value-of select="count(preceding-sibling::*[name() = name(current())]) + 1"/><xsl:text/>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

    <!-- 1/4/12: plos-specific template (prevents double punctuation if xml contains valid punctuation already) -->
    <xsl:template name="punctuation">
      <xsl:if test="not(ends-with(normalize-space(),'.')) and not(ends-with(normalize-space(),'?')) and not(ends-with(normalize-space(),'!'))">
        <xsl:text>.</xsl:text>
      </xsl:if>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (works with next two linebreak templates) -->
    <xsl:template match="text()">
      <!-- do some character transformations first-->
      <xsl:variable name="str" select="translate(., '&#8194;&#x200A;&#8764;&#x02236;&#x02208;', '  ~:&#x404;') "/>
      <xsl:choose>
        <!-- no need to progress further if the entire element is less then 40 characters -->
        <xsl:when test="string-length($str) &gt; 40">
          <xsl:call-template name="linebreaklongwords">
            <xsl:with-param name="str" select="$str" />
            <xsl:with-param name="len" select="40" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$str"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (works with following template to break long strings) -->
    <!-- break words longer then len characters -->
    <xsl:template name="linebreaklongwords">
      <xsl:param name="str"/>
      <xsl:param name="len"/>
      <xsl:for-each select="tokenize($str,'\s')">
        <xsl:choose>
          <xsl:when test="string-length(.) &gt; $len">
            <xsl:call-template name="linebreaklongwordsub">
              <xsl:with-param name="str" select="." />
              <xsl:with-param name="len" select="$len" />
              <!-- zero length space -->
              <xsl:with-param name="char"><xsl:text>&#8203;</xsl:text></xsl:with-param>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:choose>
              <xsl:when test="position()=last()">
                <xsl:copy-of select="."/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:copy-of select="."/><xsl:text> </xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (works with above template to break long strings) -->
    <xsl:template name="linebreaklongwordsub">
      <xsl:param name="str"/>
      <xsl:param name="len"/>
      <xsl:param name="char"/>
      <xsl:choose>
        <xsl:when test="string-length($str) &gt; $len">
          <xsl:value-of select="substring($str,1,$len)"/>
          <xsl:value-of select="$char"/>
          <xsl:call-template name="linebreaklongwordsub">
            <xsl:with-param name="str" select="substring($str,$len + 1)" />
            <xsl:with-param name="len" select="$len" />
            <xsl:with-param name="char" select="$char" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$str"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (used for displaying annotations) -->
    <xsl:template name="createAnnotationSpan">
      <xsl:variable name="regionId" select="@aml:id"/>
      <xsl:variable name="regionNumComments" select="number(/article/aml:regions/aml:region[@aml:id=$regionId]/@aml:numComments)"/>
      <xsl:variable name="regionNumMinorCorrections" select="number(/article/aml:regions/aml:region[@aml:id=$regionId]/@aml:numMinorCorrections)"/>
      <xsl:variable name="regionNumFormalCorrections" select="number(/article/aml:regions/aml:region[@aml:id=$regionId]/@aml:numFormalCorrections)"/>
      <xsl:variable name="regionNumRetractions" select="number(/article/aml:regions/aml:region[@aml:id=$regionId]/@aml:numRetractions)"/>
      <xsl:element name="span">
        <!-- convey the number of comments, minor/formal corrections, and retractions -->
        <xsl:attribute name="num_c"><xsl:value-of select="$regionNumComments"/></xsl:attribute>
        <xsl:attribute name="num_mc"><xsl:value-of select="$regionNumMinorCorrections"/></xsl:attribute>
        <xsl:attribute name="num_fc"><xsl:value-of select="$regionNumFormalCorrections"/></xsl:attribute>
        <xsl:attribute name="num_retractions"><xsl:value-of select="$regionNumRetractions"/></xsl:attribute>
        <!-- populate the span tag's class attribute based on the presence of comments vs. corrections -->
        <xsl:attribute name="class">
          <!-- this is always considered a note -->
          <xsl:text>note public</xsl:text>
          <xsl:if test="$regionNumMinorCorrections &gt; 0"><xsl:text> minrcrctn</xsl:text></xsl:if>
          <xsl:if test="$regionNumFormalCorrections &gt; 0"><xsl:text> frmlcrctn</xsl:text></xsl:if>
          <xsl:if test="$regionNumRetractions &gt; 0"><xsl:text> retractionCssStyle</xsl:text></xsl:if>
        </xsl:attribute>
        <xsl:attribute name="title">User Annotation</xsl:attribute>
        <xsl:attribute name="annotationId">
          <xsl:for-each select="/article/aml:regions/aml:region[@aml:id=$regionId]/aml:annotation">
            <xsl:value-of select="@aml:id"/>
            <xsl:if test="(following-sibling::aml:annotation)">
              <xsl:text>,</xsl:text>
            </xsl:if>
          </xsl:for-each>
        </xsl:attribute>
        <!-- only add an annotation to the display list if this is the beginning of the annotation -->
        <xsl:variable name="displayAnn">
        <xsl:variable name="annId" select="@aml:id"/>
        <xsl:if test="@aml:first">
          <xsl:for-each select="/article/aml:regions/aml:region[@aml:id=$regionId]/aml:annotation">
            <xsl:variable name="localAnnId" select="@aml:id"/>
            <xsl:if test="count(../preceding-sibling::aml:region/aml:annotation[@aml:id=$localAnnId]) = 0">
              <xsl:text>,</xsl:text>
              <xsl:value-of select="@aml:id"/>
            </xsl:if>
          </xsl:for-each>
        </xsl:if>
        </xsl:variable>
        <xsl:if test="not($displayAnn='')">
          <xsl:element name="a">
            <xsl:attribute name="href">#</xsl:attribute>
            <xsl:attribute name="class">bug public</xsl:attribute>
            <xsl:attribute name="id">
              <xsl:value-of select="concat('annAnchor',@aml:id)"/>
            </xsl:attribute>
            <xsl:attribute name="displayId">
            <!-- get rid of first comma in list -->
              <xsl:value-of select="substring($displayAnn,2)"/>
            </xsl:attribute>
            <xsl:attribute name="onclick">return(ambra.displayComment.show(this));</xsl:attribute>
            <xsl:attribute name="onmouseover">ambra.displayComment.mouseoverComment(this);</xsl:attribute>
            <xsl:attribute name="onmouseout">ambra.displayComment.mouseoutComment(this);</xsl:attribute>
            <xsl:attribute name="title">Click to preview this note</xsl:attribute>
          </xsl:element>
        </xsl:if>
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (used for displaying annotations (xml is coming from ambra, not article xml)) -->
    <xsl:template match="aml:annotated">
      <xsl:call-template name="createAnnotationSpan"/>
    </xsl:template>

    <!-- 1/4/12: plos-specific template (creates newlines for legibility of source html) -->
    <xsl:template name="newline1">
      <xsl:text>&#xA;</xsl:text>
	  </xsl:template>

    <!-- 1/4/12: plos-specific template (creates newlines for legibility of source html) -->
    <xsl:template name="newline2">
	    <xsl:text>&#xA;</xsl:text>
	    <xsl:text>&#xA;</xsl:text>
	  </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="append-pub-type" />
    <xsl:template name="metadata-labeled-entry" />
    <xsl:template name="metadata-entry" />
    <xsl:template name="metadata-area" />
    <xsl:template name="make-label-text" />

    <!-- 1/4/12: plos modifications -->
   	<xsl:template name="assign-id">
	    <xsl:if test="@id">
		  <xsl:attribute name="id">
		    <xsl:value-of select="@id"/>
		  </xsl:attribute>
	    </xsl:if>
	  </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="assign-src" />

    <!-- 1/4/12: plos modifications -->
    <xsl:template name="assign-href">
	    <xsl:if test="@xlink:href">
		    <xsl:attribute name="href">
		    <xsl:value-of select="@xlink:href"/>
		    </xsl:attribute>
	    </xsl:if>
	  </xsl:template>

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="named-anchor" />

    <!-- ============================================================= -->
    <!--  Process warnings                                             -->
    <!-- ============================================================= -->
    <!-- Generates a list of warnings to be reported due to processing anomalies. -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="process-warnings" />

    <!-- ============================================================= -->
    <!--  id mode                                                      -->
    <!-- ============================================================= -->
    <!-- An id can be derived for any element. If an @id is given, it is presumed unique and copied. If not, one is generated.   -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template match="*" mode="id" />
    <xsl:template match="article | sub-article | response" mode="id" />

    <!-- ============================================================= -->
    <!--  "format-date"                                                -->
    <!-- ============================================================= -->
    <!-- Maps a structured date element to a string -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="format-date" />
    <xsl:template match="day | season | year" mode="map" />

    <!-- 1/4/12: nlm contains month mode map -->

    <!-- ============================================================= -->
    <!--  "author-string" writes authors' names in sequence            -->
    <!-- ============================================================= -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="author-string" />

    <!-- ============================================================= -->
    <!--  Footer branding                                              -->
    <!-- ============================================================= -->

    <!-- 1/4/12: suppress, we don't use -->
    <xsl:template name="footer-branding" />


</xsl:stylesheet>
