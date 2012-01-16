<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.w3.org/1999/xhtml" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  
  <xsl:output method="html" indent="yes" />	

  <xsl:include href="ident.xsl" />

  <xsl:template match="xhtml:*">
    <xsl:element name="{local-name(.)}">
      <xsl:apply-templates select="@*|node()|text()" />
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>