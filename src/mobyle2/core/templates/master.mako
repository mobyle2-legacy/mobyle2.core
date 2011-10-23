<%block name="body">
  <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
      <%block name="head">
        <%block name="title">
          <title>Mobyle 2</title>
        </%block>
        <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
        <link rel="shortcut icon" href="/s/pylons.ico'"/>
        <%block name="js_slot">
        </%block>
        <%block name="css_slot">
          <link rel="stylesheet" href="/s/mobyle2.css" type="text/css" media="screen" charset="utf-8"/>
        </%block>
      </%block>
    </head>
    <body>
      <div id="wrap">
        <%block name="header">
          <div id="header">
            <%block name="header_body">
              <div class="banner-wrap">
                <%include file="includes/banner.mako"/>
              </div>
              <div class="global_tabs-wrap">
                <%include file="includes/globaltabs.mako"/>
              </div>
              <div class="breadcrumbs-wrap">
                <%include file="includes/breadcrumbs.mako"/>
              </div>
            </%block>
          </div>
        </%block>
        <div id="content">
          <%block name="content">
            <%block name="right_slot">
              <div class="right_slot">
              </div>
            </%block>
            <%block name="middle_slot">
              <div class="middle_slot">
                <div id="above-content">
                  <%block name="above_content">
                  </%block>
                </div>
                <div id="content-body">
                  <%block name="content_body">
                  </%block>
                </div>
                <div id="bottom">
                  <%block name="below_content">
                  </%block>
                </div>
              </div>
            </%block>
            <%block name="left_slot">
              <div class="left_slot">
              </div>
            </%block>
          </%block>
        </div>
        <div id="bottom">
          <%block name="footer">
            <div id="footer">
              <%block name="footer_body">
              </%block>
              <%block name="colophon">
              </%block>
            </div>
          </%block>
        </div>
      </div>
    </body>
  </html>
</%block>

