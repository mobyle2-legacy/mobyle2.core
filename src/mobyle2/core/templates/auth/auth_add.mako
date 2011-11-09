<%inherit file="../master.mako"/>
<%block name="content_body">
  <h1>${_('Backend configuration')}</h1>
  <div id="add_auth_backend_holder">
    ${f_content | n}
  </div>
  <script language="JavaScript">
    $(document).ready(function() {
      deform.load();
      function set_add_params(data) {
        $('#add_auth_backend_holder > *').remove();
        $('#add_auth_backend_holder').append($(data));
        bind_auth_events();
      } 
      function bind_auth_events() {
        $("*[name='auth_backend']").change(
        function() {
          data = $('#add_auth_backend').serializeArray();
          data[data.length] = {'name': 'load_auth_backend_details', 
            'value': $('*[name=auth_backend]').val()
          };
          $.ajax({
            url: '',
            type: 'POST',
            data: data,
            success: set_add_params,
            dataType: 'html'
          }); 
      })};
      bind_auth_events();
    });
  </script>
</%block>