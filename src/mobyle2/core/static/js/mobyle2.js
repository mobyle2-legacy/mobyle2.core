$(document).ready(function() {
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

