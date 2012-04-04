<?xml version="1.0" encoding="utf-8"?>
<!-- 
	form.xsl stylesheet
	Authors: Hervé Ménager
-->
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.w3.org/1999/xhtml" xmlns:xhtml="http://www.w3.org/1999/xhtml">

	<!-- this uri is the identifier of the program xml, i.e., the url of the xml definition on its execution server --> 
	<xsl:param name="programUri" />	

	<!-- this uri is the identifier of the program xml, i.e., the url of the xml definition on its execution server --> 
	<xsl:param name="programPID" /> 

	<xsl:variable name="server" select="substring-before($programPID,'.')" />
	
	<xsl:include href="ident.xsl" />

	<xsl:template match="/|comment()|processing-instruction()">
		<xsl:copy>
			<!-- go process children (applies to root node only) -->
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="*">
		<xsl:element name="{local-name()}">
			<!-- go process attributes and children -->
			<xsl:apply-templates select="@*|node()"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="@*">
		<xsl:attribute name="{local-name()}">
			<xsl:value-of select="."/>
		</xsl:attribute>
	</xsl:template>	

	<xsl:template match="/">
		<form action="session_job_submit.py" id="{$programPID}" class="program">
			<table class="header">
				<tr>
					<td style="width: 60%">
						<xsl:apply-templates select="*/head" mode="serviceHeader"/>						
					</td>
					<td>
						<xsl:apply-templates select="*/head" mode="formHeader"/>						
					</td>
				</tr>
			</table>
			<xsl:apply-templates select="*/head/doc/comment" mode="ajaxTarget"/>
			<xsl:apply-templates select="*/flow"/>
			<xsl:apply-templates select="*/head/interface[@type='form']/*" />
			<xsl:apply-templates select="*/head" mode="serviceFooter"/>
			
		</form>
	</xsl:template>

	<xsl:template match="flow">
		<xsl:text disable-output-escaping="yes">&lt;![if !IE]&gt;</xsl:text>
			<fieldset class="minimizable">
				<legend>Workflow details</legend>
				<center>
					<object data="workflow_layout.py?id={$programPID}">
						<iframe width="100%" src="workflow_layout.py?id={$programPID}" />
					</object>
				</center>
			</fieldset>
		<xsl:text disable-output-escaping="yes">&lt;![endif]&gt;</xsl:text>
	</xsl:template>

	<xsl:template match="head" mode="formHeader">
		<span>
			<input type="submit" value="Run" />
			<input type="reset" value="Reset" />
			<xsl:if test="/program">
				<input type="hidden" name="programName" value="{$programUri}" />
			</xsl:if>
			<xsl:if test="/workflow">
				<input type="hidden" name="workflowUrl" value="{$programUri}" />
			</xsl:if>
		</span>
	</xsl:template>	

</xsl:stylesheet>
