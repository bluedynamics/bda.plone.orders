(function($) {
    
    $(document).ready(function() {
        var url = $('#bdaploneorders').attr('data-ajaxurl');
        var oTable = $('#bdaploneorders').dataTable({
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": url,
            "sPaginationType": "full_numbers",
            "oLanguage": {
                "sUrl": "@@collective.js.datatables.translation"
            },
            "aoColumnDefs": [{
                'bSortable': false,
                'aTargets': [0]
            }],
            "aaSorting": [[1, "desc"]],
            "fnDrawCallback": orders.bind
        });
        $.extend(bdajax.binders, {
            orders_dropdown_menus: orders.dropdown_binder
        });
        orders.dropdown_binder(document);
    });
    
    var orders = {
        bind: function() {
            $(this).bdajax();
        },
        
        dropdown_binder: function(context) {
            var sel = '.change_reservation_booking_state_dropdown';
            $(sel, context).dropdownmenu({
                menu: '.dropdown_items',
                trigger: '.change_reservation_booking_state strong'
            });
        }
    }
    
    $.fn.dropdownmenu = function(options) {
        var trigger = options.trigger;
        var menu = options.menu;
        this.unbind('click');
        $(trigger, this).bind('click', function(event) {
            event.preventDefault();
            var container = $(menu, $(this).parent().parent());
            $(document).unbind('mousedown')
                       .bind('mousedown', function(event) {
                if ($(event.target).parents(menu + ':first').length) {
                    return true;
                }
                container.css('display', 'none');
            });
            container.css('display', 'block');
        });
        return this;
    }

})(jQuery);