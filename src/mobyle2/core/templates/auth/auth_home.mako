<%inherit file="../master.mako"/>
<%block name="content_body">
  <p>${_("Authentication backends configuration")}</p>
  <ul>
    <li><a href="@@manage-settings">${_('Edit general authentication settings')}</a></li>
    <li><a href="@@list">${_('List backends')}</a></li>
  </ul>
</%block>
