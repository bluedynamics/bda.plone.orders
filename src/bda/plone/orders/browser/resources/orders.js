(function ($) {

    $(document).ready(function () {
        $.extend(bdajax.binders, {
            orders_datatable_binder: orders.datatable_binder,
            orders_filter_binder: orders.filter_binder,
            orders_dropdown_menus: orders.dropdown_binder,
            orders_notification_form_binder: orders.notification_form_binder,
            orders_qr_code_binder: orders.qr_code_binder
        });
        orders.datatable_binder(document);
        orders.filter_binder(document);
        orders.order_select_binder(document);
        orders.notification_binder(document);
        orders.qr_code_binder(document);
    });

    var orders = {

        qr_code_binder: function(context) {
            $('.qr_code', context).each(function() {
                var elem = $(this);
                var text = elem.data('text');
                var width = elem.data('width');
                var height = elem.data('height');
                var qrcode = new QRCode(elem.get(0), {
                    text: text,
                    width: width,
                    height: height,
                    colorDark : "#000000",
                    colorLight : "#ffffff",
                    correctLevel : QRCode.CorrectLevel.H
                });
            });
        },

        datatable_binder: function(context) {
            var url = $('#bdaploneorders', context).attr('data-ajaxurl');
            var oTable = $('#bdaploneorders', context).dataTable({
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
        },

        filter_binder: function(context) {
            $('#input-vendor').unbind('change')
                              .bind('change', orders.filter_orders);
            $('#input-customer').unbind('change')
                                .bind('change', orders.filter_orders);
        },

        filter_orders: function(event) {
            event.preventDefault();
            var selection = $(this);
            var wrapper = selection.parent();
            var vendor, customer;
            if (selection.attr('name') == 'vendor') {
                vendor = selection.val();
                customer = $('#input-customer', wrapper).val();
            } else {
                vendor = $('#input-vendor', wrapper).val();
                customer = selection.val();
            }
            var ajax_table = wrapper.parents('.ajaxtable');
            var action = ajax_table.data('tablename');
            var target = bdajax.parsetarget(wrapper.attr('ajax:target'));
            target.params['vendor'] = vendor;
            target.params['customer'] = customer;
            bdajax.action({
                name: action,
                selector: '#orders_wrapper',
                mode: 'inner',
                url: target.url,
                params: target.params
            });
        },

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

        notification_form_binder: function(context) {
            var form = $('#form-notify_customers');
            $(orders.selected_order_uids()).each(function() {
                form.append('<input type="hidden" ' +
                                   'name="uids:list" ' +
                                   'value="' + this + '" />');
            });
            $('#input-notify_customers-template').change(function(event) {
                var url = $('#input-notify_customers-template').data('tplurl');
                $.ajax({
                    url: url,
                    data: {name: $('#input-notify_customers-template').val()},
                    success: function(data, status, request) {
                        $('#input-notify_customers-text').val(data.tpl);
                    }
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

})(jQuery);
