(function() {
  (function($) {
    return $.fn.ajaxChosen = function(ajaxoptions, callback, chozenopts) {
      if (chozenopts == null) {
        chozenopts = {};
      }
      if(chozenopts.typingTimeout == null){
        chozenopts.typingTimeout = 500;
      }
      var KEY = {ESC:27,RETURN:13,TAB:9,BS:8,DEL:46,UP:38,DOWN:40};
      select = this;
      function startTypingTimeout(e, element) {
        $.data(element, "typingTimeout", window.setTimeout(function() {
          $(e.target || e.srcElement).triggerHandler("ajaxchosen");
        }, chozenopts.typingTimeout));
      }
      function handleKeyDownUp(e) {
         var k = e.which || e.keycode;
         if ((k == KEY.UP || k == KEY.DOWN) && !$.data(this, "typingTimeout")) {
           startTypingTimeout(e, this);
         } else if (k == KEY.BS || k == KEY.DEL) {
           var typingTimeout = $.data(this, "typingTimeout");
           if (typingTimeout) {
             window.clearInterval(typingTimeout);
           }
           startTypingTimeout(e, this);
         }
      };
      function handleKeyPress(e) {
        var typingTimeout = $.data(this, "typingTimeout");
        var k = e.keyCode || e.which; // keyCode == 0 in Gecko/FF on keypress
        if(typingTimeout) {
          window.clearInterval(typingTimeout);
        }
        if($.data(document.body, "suppressKey")) {
          return $.data(document.body, "suppressKey", false);
        } else if($.data(document.body, "autocompleteMode") && k < 32 && k != KEY.BS && k != KEY.DEL) {
          return false;
        } else if (k == KEY.BS || k == KEY.DEL || k > 32) { // more than ESC and RETURN and the like
          startTypingTimeout(e, this);
        }
      }
      this.chosen(chozenopts);
      return this.next(
          '.chzn-container'
      ).find("*[class=chzn-search or class=search-field] > input")
      .keydown(handleKeyDownUp)
      .keyup(handleKeyDownUp)
      .keypress(handleKeyPress)
      .bind('ajaxchosen', 
        function() {
        var field, val;
        val = $.trim($(this).attr('value'));
        if (val.length < 3 || val === $(this).data('prevVal')) {
          return false;
        }
        $(this).data('prevVal', val);
        field = $(this);
        ajaxoptions.data = {term: val};
        if (typeof success !== "undefined" && success !== null) {
          success;
        } else {
          success = ajaxoptions.success;
        };
        ajaxoptions.success = function(data) {
          var items;
          if (!(data != null)) {
            return;
          }
          select.find('option').each(function() {
            if (!$(this).is(":selected")) {
              return $(this).remove();
            }
          });
          items = callback(data);
          $.each(items, function(value, text) {
            return $("<option />").attr('value', value).html(text).appendTo(select);
          });
          select.trigger("liszt:updated");
          field.attr('value', val);
          if (typeof success !== "undefined" && success !== null) {
            return success();
          }
        };
        return $.ajax(ajaxoptions);
      });
    };
  })(jQuery);
}).call(this);

