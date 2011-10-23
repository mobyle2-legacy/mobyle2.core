<%inherit file="../master.mako"/>
head()
<%block name="content_body">
  <h1>List of projects</h1>
<ul>
  % for name, project in c.items.iteritems():
<li>
    <a href="${u(project, request)}">${name}</a>
</li>
  % endfor
</ul>
</%block>
