$(document).ready(function() {
  $('#left_menu').resizable({ handles: 'e' });
  deform.load();
  $('.mobyle2-datatables').each(
    function(i, o){
      $(o).dataTable(
        {
              "bJQueryUI": true
        }
      );
  });
});

