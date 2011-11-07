<%block name="breadcrumbs">
  <div id="breadcrumbs">
    <p class="title">${_('You are here')}:</p>
    <ul>
      % for i in v.get_breadcrumbs():
      <li class="${i['class']}">
      <a href="${i['url']}">${i['name']}</a>
      </li>
      % endfor
    </ul>
  </div>
</%block>
