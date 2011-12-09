(function() {
  (function($) {
    return $.fn.ajaxChosen = function(ajaxoptions, callback, chozenopts) {
      var KEY = {ESC:27,RETURN:13,TAB:9,BS:8,DEL:46,UP:38,DOWN:40};
      var select = this;
      if (chozenopts == null) {
        chozenopts = {};
      }
      if(chozenopts.typingTimeout == null){
        chozenopts.typingTimeout = 500;
      }
      function hide_no_results() {
        $('.no-results', $(select).parents('div')).hide();
      }
      function startTypingTimeout(e, element) {
        var target = $(e.target || e.srcElement);
        $.data(element, 
          "typingTimeout", 
          window.setTimeout(
              function() {
                target.triggerHandler("ajaxchosen");
              },
              chozenopts.typingTimeout)
        );
      }
      function handleKeyDownUp(e) {
         var k = e.which || e.keycode;
         var target = $(e.target || e.srcElement);
         if ((k == KEY.UP || k == KEY.DOWN) && !$.data(target, "typingTimeout")) {
           startTypingTimeout(e, target);
         } else if (k == KEY.BS || k == KEY.DEL) {
           var typingTimeout = $.data(target, "typingTimeout");
           if (typingTimeout) {
             window.clearInterval(typingTimeout);
           }
           startTypingTimeout(e, target);
         }
        hide_no_results();
      };
      function handleKeyPress(e) {
        var target = $(e.target || e.srcElement);
        var typingTimeout = $.data(target, "typingTimeout");
        var k = e.keyCode || e.which; // keyCode == 0 in Gecko/FF on keypress
        if(typingTimeout) {
          window.clearInterval(typingTimeout);
        }
        if($.data(document.body, "suppressKey")) {
          return $.data(document.body, "suppressKey", false);
        } else if($.data(document.body, "autocompleteMode") && k < 32 && k != KEY.BS && k != KEY.DEL) {
          return false;
        } else if (k == KEY.BS || k == KEY.DEL || k > 32) { // more than ESC and RETURN and the like
          startTypingTimeout(e, target);
        }
        hide_no_results();
      }
      select.chosen(chozenopts);
      return select.next('.chzn-container').find("*[class=chzn-search or class=search-field] > input")
      .keydown(handleKeyDownUp)
      .keyup(handleKeyDownUp)
      .keypress(handleKeyPress)
      .bind('ajaxchosen', 
        function(e) {
           var target = $(e.target || e.srcElement);
           var curselect = $('select', target.parents('.chzn-container').parent()); 
           var inputC = $(target).parent('li');
           var field, val;
           hide_no_results();
           val = $.trim($(target).attr('value'));
           if (val.length < 3 || val === $(target).data('prevVal')) {
             return false;
           }
           $(target).data('prevVal', val);
           field = $(target);
           ajaxoptions.data = {term: val};
           if (typeof success !== "undefined" && success !== null) {
             success();
           } else {
             success = ajaxoptions.success;
           };
           ajaxoptions.beforeSend = function(xhr, settings) {
             inputC.prepend('<div class="chosen-loading-spinner" alt="Wait">&nbsp;</div>');
           }
           ajaxoptions.complete = function(xhr, settings) {
             $('div.chosen-loading-spinner', inputC).remove();
           }  
           ajaxoptions.success = function(data) {
             var items;
             if (!(data != null)) {return;}
             target.find('option').each(function(i, item) {
               if (!$(item).is(":selected")) {
                 $(item).remove();
               }
             });
             items = callback(data);
             var current_opts_ids = new Array();
             $('option', target).each(function(i, val){current_opts_ids.push(val.value);});
             $.each(items, function(value, text) {
               if($.inArray(value, current_opts_ids)==-1) {
                 $("<option />").attr('value', value).html(text).appendTo(curselect);
                 current_opts_ids.push(value);
               }
             });
             curselect.trigger("liszt:updated");
             field.attr('value', val);
             if (typeof success !== "undefined" && success !== null) {
               return success();
             }
           };
           return $.ajax(ajaxoptions);
        }
      );
    };
  })(jQuery);
}).call(this);

