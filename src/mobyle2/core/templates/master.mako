<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
    <head>
        <%block name="head">
            <%block name="title">
                <title>Mobyle 2</title>
            </%block>
            <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
            <link rel="shortcut icon" href="${request.static_url('birdie:static/favicon.ico')}"/>
            <%block name="js_slot">
            </%block>
            <%block name="css_slot">
                <link rel="stylesheet" href="${request.static_url('birdie:static/pylons.css')}" type="text/css" media="screen" charset="utf-8" />
                <link rel="stylesheet" href="http://static.pylonsproject.org/fonts/nobile/stylesheet.css" media="screen"/>
                <link rel="stylesheet" href="http://static.pylonsproject.org/fonts/neuton/stylesheet.css" media="screen"/>
            </%block> 
        </%block>
    </head>
    <body>
        <%block name="body">
            <div id="wrap">
                <div id="header">
                    <%block name="header">
                    </%block>
                </div>
                <div id="content">
                    <%block name="content">
                        <%block name="above-content">
                            <div id="above-content"></div>
                        </%block> 
                        <div id="content">
                            <%block name="contentbody">
                            </%block>
                        </div>
                        <div id="bottom">
                            <%block name="below-content">
                            </%block> 
                        </div>
                    </%block>
                </div>
                <div id="bottom">
                    <%block name="footer">
                        <div id="footer">
                            <%block name="footer">
                            </%block>
                        </div>
                    </%block>
                </div>
            </div>
        </%block>
    </body>
</html>  
