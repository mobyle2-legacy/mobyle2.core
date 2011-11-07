<%inherit file="../master.mako"/>
<%block name="content_body">
  <form method="post">
    <input type="hidden" name="submitted" value="1"/>
    <input type="submit" name="reload" value="Reload the webserver"/>
  </form> 
</%block> 
