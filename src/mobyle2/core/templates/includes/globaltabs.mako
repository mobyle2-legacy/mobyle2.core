<%block name="globaltabs">
  <div id="globaltabs">
    <ul>
      % for i in v.get_globaltabs():
      <li class="${i['class']}">
      <a href="${i['url']}">${i['name']}</a>
      </li>
      % endfor
    </ul>
  </div>
</%block>
