(function ($) {

    $(document).ready(function () {
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
        orders.order_select_binder(document);
        orders.notification_binder(document);
    });

    var orders = {
        bind: function () {
            orders.do_order_selection($('input[name="select_all_orders"]'));
            $(this).bdajax();
        },

        do_order_selection: function(cb) {
            var cbs = $('input.select_order');
            if (cb.is(':checked')) {
                cbs.attr('checked','checked');
            } else {
                cbs.removeAttr('checked');
            }
        },

        order_select_binder: function(context) {
            $('input[name="select_all_orders"]')
                .unbind('change')
                .bind('change', function(event) {
                    orders.do_order_selection($(this));
                });
        },

        selected_order_uids: function() {
            var uids = new Array();
            $('input:checkbox[name=select_order]:checked').each(function() {
                uids.push($(this).val());
            });
            return uids;
        },

        notification_binder: function(context) {
            $('a.notify_customers', context).bind('click', function(evt) {
                evt.preventDefault();
                var elem = $(this);
                var target = elem.attr('ajax:target');
                var uids = orders.selected_order_uids();
                if (uids.length === 0) {
                    bdajax.warning('No Orders Selected.');
                    return;
                }
                bdajax.overlay({
                    'action': 'notify_customers',
                    'target': target
                });
            });
        },

        dropdown_binder: function (context) {
            var sel = '.change_order_salaried_dropdown';
            $(sel, context).ordersdropdownmenu({
                menu: '.dropdown_items',
                trigger: '.dropdown_header'
            });
            sel = '.change_order_state_dropdown';
            $(sel, context).ordersdropdownmenu({
                menu: '.dropdown_items',
                trigger: '.dropdown_header'
            });
        }
    };

    $.fn.ordersdropdownmenu = function (options) {
        var trigger = options.trigger;
        var menu = options.menu;
        this.unbind('click');
        $(trigger, this).bind('click', function (event) {
            event.preventDefault();
            var container = $(menu, $(this).parent().parent());
            $(document).unbind('mousedown')
                       .bind('mousedown', function (event) {
                if ($(event.target).parents(menu + ':first').length) {
                    return true;
                }
                container.css('display', 'none');
            });
            container.css('display', 'block');
        });
        return this;
    };

}(jQuery));
