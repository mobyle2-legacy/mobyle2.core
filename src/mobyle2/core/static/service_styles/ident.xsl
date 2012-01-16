<?xml version="1.0" encoding="utf-8"?>
<!-- 
	ident.xsl stylesheet
	Authors: Hervé Ménager
-->
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"  xmlns:xhtml="http://www.w3.org/1999/xhtml">
	<!-- This stylesheet contains the XSL Identity Transform used by many other stylesheets -->

	<xsl:template match="@*|node()|text()" priority="-1">
		<xsl:call-template name="nodeCopy" />
	</xsl:template>

	<xsl:template name="nodeCopy">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()|text()" />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="type" mode="label">
		<!-- processing parameter type to display it in the parameter label if relevant (i.e., "bio-related" type) -->
		<xsl:variable name ="dataType">
			<xsl:choose>
				<xsl:when test="datatype/superclass"><xsl:value-of select="datatype/superclass"/></xsl:when>
				<xsl:otherwise><xsl:value-of select="datatype/class"/></xsl:otherwise>
			</xsl:choose>
		</xsl:variable>		
		<xsl:if test="not(($dataType = 'Choice') or ($dataType = 'MultipleChoice') or ($dataType = 'Boolean') or ($dataType = 'Integer') or ($dataType = 'Float') or ($dataType = 'String') or ($dataType = 'Filename') or ($dataType = 'Binary'))">
			<xhtml:i>
				(<xsl:if test="biotype">
					<xsl:for-each select="biotype">
						<xsl:value-of select="text()" />
						<xsl:if test="position()!= last()"><xsl:text> or </xsl:text></xsl:if>
					</xsl:for-each>
					<xsl:text> </xsl:text>
				</xsl:if>
				<xsl:value-of select="datatype/class/text()" />)
			</xhtml:i>
		</xsl:if>
	</xsl:template>	

	<xsl:attribute-set name="param">
		<!-- 
			<xsl:attribute name="id"><xsl:value-of select="//parameter[(name/text()=current()/@data-parametername)]/name/text()"/></xsl:attribute>
		-->
		<xsl:attribute name="class">
			<!-- "parameter" class defines the outer element for a parameter that groups a set of controls -->
			<xsl:text>parameter </xsl:text>
			<xsl:if test="//parameter[(name/text()=current()/@data-parametername) and @ismandatory and @ismandatory='1']">
				mandatory
				<xsl:if test="//parameter[(name/text()=current()/@data-parametername) and ancestor-or-self::*/precond]"><xsl:text> conditional</xsl:text></xsl:if>
			</xsl:if>
		</xsl:attribute>
		<xsl:attribute name="title">
			<!-- help text for mandatory parameters -->
			<xsl:if test="//parameter[(name/text()=current()/@data-parametername) and @ismandatory and @ismandatory='1']">
				<xsl:text>This parameter is mandatory</xsl:text><xsl:if test="//parameter[(name/text()=current()/@data-parametername) and ancestor-or-self::*/precond]"><xsl:text> under certain conditions.</xsl:text></xsl:if>
			</xsl:if>
		</xsl:attribute>
		<xsl:attribute name="data-datatype"><xsl:value-of select="//parameter[name/text()=current()/@data-parametername]/type/datatype/class/text()" /></xsl:attribute>
		<xsl:attribute name="data-datatype-superclass"><xsl:value-of select="//parameter[name/text()=current()/@data-parametername]/type/datatype/superclass/text()" /></xsl:attribute>		
		<xsl:attribute name="data-biotype">
			<xsl:for-each select="//parameter[name/text()=current()/@data-parametername]/type/biotype">
				<xsl:value-of select="text()" /><xsl:text> </xsl:text>
			</xsl:for-each>
		</xsl:attribute>
		<xsl:attribute name="data-card">
			<xsl:value-of select="//parameter[name/text()=current()/@data-parametername]/type/card/text()" />
		</xsl:attribute>
		<xsl:attribute name="data-formats">
			<xsl:for-each select="//parameter[name/text()=current()/@data-parametername]/type//dataFormat">
				<xsl:value-of select="text()" /><xsl:text> </xsl:text>
			</xsl:for-each>
		</xsl:attribute>
	</xsl:attribute-set>
	
	<xsl:template match="head" mode="serviceHeader">
			<xhtml:h1>
				<xsl:if test="package/doc/title/text()">
					<xsl:value-of select="package/doc/title/text()" />
					<xsl:if test="package/version">
						<xsl:text> </xsl:text>
						<xsl:value-of select="package/version/text()"/>
					</xsl:if>:
				</xsl:if>
				<xsl:value-of select="doc/title/text()" />
				<xsl:if test="$server">@<xsl:value-of select="$server"/></xsl:if>
				<xsl:if test="version">
					<xsl:text> </xsl:text>
					<xsl:value-of select="version/text()"/>
				</xsl:if>
				<xsl:apply-templates select="doc/comment" mode="ajaxLink"/>
			</xhtml:h1>
			<!-- Description -->
			<xhtml:h2>
				<xsl:copy-of select="doc/description/text/text()" />
			</xhtml:h2>
	</xsl:template>

	<xsl:template match="head" mode="serviceFooter">
		<xhtml:div class="info">
			<xsl:if test="package/doc/description/text/text()">
				<xhtml:h4><xsl:copy-of select="package/doc/description/text/text()" /></xhtml:h4>
			</xsl:if>
			<xsl:apply-templates select="package/doc/reference" mode="serviceFooter"/>
			<xsl:apply-templates select="doc/reference" mode="serviceFooter"/>
			<xsl:apply-templates select="package/doc/authors" mode="serviceFooter"/>
			<xsl:apply-templates select="doc/authors" mode="serviceFooter"/>
			<xsl:apply-templates select="package/doc/doclink" mode="serviceFooter"/>
			<xsl:apply-templates select="doc/doclink" mode="serviceFooter"/>
		</xhtml:div>
	</xsl:template>
	
	<xsl:template match="reference" mode="serviceFooter">
		<!-- Reference Link -->
		<xhtml:div class="reference">
			<xsl:choose>
				<xsl:when test="@url or @doi">
					<xhtml:a target="_blank">
						<xsl:choose>
							<xsl:when test="@url">
								<xsl:attribute name="href"><xsl:value-of select="@url"/></xsl:attribute>
							</xsl:when>
							<xsl:when test="@doi">
								<xsl:attribute name="href">http://dx.doi.org/<xsl:value-of select="@doi"/></xsl:attribute>
							</xsl:when>
						</xsl:choose>
						<xsl:copy-of select="child::node()" />
					</xhtml:a>
				</xsl:when>
				<xsl:otherwise>
					<xsl:copy-of select="child::node()" />					
				</xsl:otherwise>
			</xsl:choose>
		</xhtml:div>		
	</xsl:template>
	
	<xsl:template match="authors" mode="serviceFooter">
		<xhtml:div class="authors"><xsl:copy-of select="child::node()" /></xhtml:div>
	</xsl:template>
	
	<xsl:template match="doclink" mode="serviceFooter">
		<xhtml:a>
			<xsl:attribute name="href">
				<xsl:value-of select="." />
			</xsl:attribute>
			<xsl:value-of select="." />
		</xhtml:a>
	</xsl:template>

	<xsl:template match="comment" mode="ajaxLink">
		<xhtml:a href="#{generate-id(..)}::comment" class="blindLink commentToggle" onclick="if (typeof portal=='undefined'){{var target=document.getElementById(this.getAttribute('href').substr(1)); target.style.display=(target.style.display=='none') ? '':'none';}}" title="click to expand/collapse contextual help">?</xhtml:a>        
	</xsl:template>
	
	<xsl:template match="comment" mode="ajaxTarget">
		<xsl:choose>
			<xsl:when test="text">
				<xhtml:div id="{generate-id(..)}::comment" class="commentText" style="display:none" mode="ajaxTarget">
					<xsl:apply-templates select="text" mode="ajaxTarget"/>
					<xsl:apply-templates select="../example" mode="exampleInclude"/>
				</xhtml:div>
			</xsl:when>
			<xsl:otherwise>
				<xhtml:div id="{generate-id(..)}::comment" class="commentText" style="display:none" mode="ajaxTarget">
					<xsl:copy-of select="xhtml:*|text()" />     
					<xsl:apply-templates select="../example" mode="exampleInclude"/>
				</xhtml:div>
			</xsl:otherwise>            
		</xsl:choose>
	</xsl:template>

	<xsl:template match="comment" mode="ajaxTargetJob">
		<xsl:choose>
			<xsl:when test="text">
				<xhtml:div id="{generate-id(..)}::comment" class="commentText" style="display:none" mode="ajaxTarget">
					<xsl:apply-templates select="text" mode="ajaxTarget"/>
				</xhtml:div>
			</xsl:when>
			<xsl:otherwise>
				<xhtml:div id="{generate-id(..)}::comment" class="commentText" style="display:none" mode="ajaxTarget">
					<xsl:copy-of select="xhtml:*|text()" />     
				</xhtml:div>
			</xsl:otherwise>            
		</xsl:choose>
	</xsl:template>	

	<xsl:template match="comment/text" mode="ajaxTarget">
		<xhtml:div><xsl:apply-templates select="text()" /></xhtml:div>
	</xsl:template>

</xsl:stylesheet>