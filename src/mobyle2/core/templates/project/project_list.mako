<%inherit file="../master.mako"/>
head()
<%block name="content_body">
  <h1>List of projects</h1>
<ul>
  % for project in projects):
<li>
    <a href="${u(request.context, request)}/project.id">${project.namename}</a>
</li>
  % endfor
</ul>
</%block>
