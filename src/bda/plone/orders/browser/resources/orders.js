/* jslint browser: true */
/* global jQuery, bdajax, QRCode */
(function ($, bdajax, QRCode) {
    "use strict";

    $(document).ready(function () {
        $.extend(bdajax.binders, {
            orders_datatable_binder: orders.datatable_binder,
            orders_filter_binder: orders.filter_binder,
            orders_bookings_datatable_binder: orders.bookings_datatable_binder,
            orders_contacts_datatable_binder: orders.contacts_datatable_binder,
            orders_dropdown_menus: orders.dropdown_binder,
            orders_notification_binder: orders.notification_binder,
            orders_notification_form_binder: orders.notification_form_binder,
            orders_qr_code_binder: orders.qr_code_binder,
            cancel_confirm_binder: orders.cancel_confirm_binder,
            comment_edit_binder: orders.comment_edit_binder
        });
        orders.datatable_binder(document);
        orders.filter_binder(document);
        orders.bookings_datatable_binder(document);
        orders.contacts_datatable_binder(document);
        orders.order_select_binder(document);
        orders.notification_binder(document);
        orders.qr_code_binder(document);
        orders.cancel_confirm_binder(document);
        orders.comment_edit_binder(document);
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
            // if the table gets called with a hash (this happens on the contacts
            // site) then the table gets initialized via oSearch to only show orders
            // that match the given email
            var hash = window.location.hash.substring(1);
            //hide customer filter if hash is sent
            if (hash) {
                $('.filter').hide();
            }

            $('#bdaploneorders', context).dataTable({
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
                "oSearch": {"sSearch": hash},
                "fnDrawCallback": orders.bind
            });
        },

        filter_binder: function(context) {
            $('#input-vendor').unbind('change')
                              .bind('change', orders.filter_orders);
            $('#input-customer').unbind('change')
                                .bind('change', orders.filter_orders);
            $('#input-state').unbind('change')
                             .bind('change', orders.filter_orders);
            $('#input-salaried').unbind('change')
                                .bind('change', orders.filter_orders);
        },

        cancel_confirm_binder: function(context) {
            $('.booking-cancel-link', context).bind('click', function(evt) {
                evt.preventDefault();
                var options = {
                    message: 'Are you sure?',
                    url: $(this).attr('href')
                };
                bdajax.dialog(options, function(options) {
                    window.location.href = options.url;
                });
            });
        },

        comment_edit_binder: function(event) {
            $('.booking_comment_edit_action')
                .unbind('click')
                .bind('click', orders.comment_edit_start);
            $('.booking_comment_save_action')
                .unbind('click')
                .bind('click', orders.comment_edit_save);
            $('.booking_comment_abort_action')
                .unbind('click')
                .bind('click', orders.comment_edit_abort);

        },
        comment_edit_start: function(event) {
            event.preventDefault();
            $(this).parent().find('.booking_comment_display').hide();
            $(this).parent().find('.booking_comment_edit').show();
        },
        comment_edit_save: function(event) {
            event.preventDefault();
            var parent = $(this).parent();
            parent.find('.booking_comment_spinner').show();
            parent.find('.booking_comment_edit').hide();
            var input = $(parent.find('input'));
            var uid = input.data('booking-uid');
            var url = input.data('edit-url');
            $.ajax({
                url: url,
                data: {uid: uid, comment: input.val()}
            })
            .done(function(data, status, request) {
                parent.find('.booking_comment_text').text(input.val());
                parent.find('.booking_comment_spinner').hide();
                parent.find('.booking_comment_display').show();
            })
            .fail(function(data, status, request) {
                window.alert('Server error!');
                input.val(
                    parent.find('.booking_comment_text').text()
                );
                parent.find('.booking_comment_spinner').hide();
                parent.find('.booking_comment_display').show();
            });
        },
        comment_edit_abort: function(event) {
            event.preventDefault();
            $(this).parent().find('.booking_comment_display').show();
            $(this).parent().find('.booking_comment_edit').hide();
        },


        filter_orders: function(event) {
            event.preventDefault();
            var selection = $(this);
            var wrapper = selection.closest('.filter');
            var vendor = $('#input-vendor', wrapper).val();
            var customer = $('#input-customer', wrapper).val();
            var state = $('#input-state', wrapper).val();
            var salaried = $('#input-salaried', wrapper).val();

            var ajax_table = wrapper.closest('.ajaxtable');
            var action = ajax_table.data('tablename');
            var target = bdajax.parsetarget(wrapper.attr('ajax:target'));
            target.params.vendor = vendor;
            target.params.customer = customer;
            target.params.state = state;
            target.params.salaried = salaried;

            var selector = '#orders_wrapper';
            if (!$('#orders_wrapper').length) {
                selector = '#bookings_wrapper';
                target.params.group_by = $('#input-group_by').val();
            }

            bdajax.action({
                name: action,
                selector: selector,
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
            var uids = [];
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

        bookings_datatable_binder: function (context) {
            var url = $('#bdaplonebookings', context).attr('data-ajaxurl');
            // if the table gets called with a hash (this happens on the contacts
            // site) then the table gets initialized via oSearch to only show orders
            // that match the given email
            var hash = window.location.hash.substring(1);
            var oTable;
            oTable = $('#bdaplonebookings', context).DataTable({
                "sort": false,
                "dom": 'l<"customfilter">frtip',
                "processing": true,
                "serverSide": true,
                "ajax": {
                    "url": url,
                    "data": function (d) {
                        return $.extend({}, d, {
                            "vendor": $('#input-vendor').val(),
                            "customer": $('#input-customer').val(),
                            "state": $('#input-state').val(),
                            "salaried": $('#input-salaried').val(),
                            "group_by": $('#input-group_by').val(),
                            "from_date": $('#input-from_date').val(),
                            "to_date": $('#input-to_date').val()
                        });
                    }
                },
                "paginationType": "full_numbers",
                "lengthMenu": [
                    [3, 5, 10, 20],
                    [3, 5, 10, 20]
                ],
                "displayLength": 3,
                "language": {
                    "url": "@@collective.js.datatables.translation"
                },
                "columnDefs": [
                    {
                        'visible': false,
                        'targets': [0, 1, 11, 12]  // hide Email, buyable_uid, bookings_quantity, bookings_total_sum
                    }
                ],

                "sorting": [
                    [1, "desc"]
                ],
                "oSearch": {"sSearch": hash},

                "initComplete": function () {
                    $(".group_filter").detach().appendTo('.customfilter');
                    //$(".date_from_filter").detach().appendTo('.customfilter');
                    //$(".date_to_filter").detach().appendTo('.customfilter');
                    $('#input-group_by').change(function () {
                        oTable.search($('#bdaplonebookings_filter input').val()).draw();
                    });
                    $('#input-from_date').on('keyup click', function () {
                        oTable.search($('#bdaplonebookings_filter input').val()).draw();
                    });
                    $('#input-to_date').on('keyup click', function () {
                        oTable.search($('#bdaplonebookings_filter input').val()).draw();
                    });
                },

                "drawCallback": function (settings) {
                    var api = this.api();
                    var rows = api.rows({page: 'current'}).nodes();
                    var last = null;
                    // only show email info if grouped by email
                    if ($('#input-group_by').val() === 'email') {
                        api.column(0, {page: 'current'}).data().each(function (group, i) {
                            if (last !== group) {
                                $(rows).eq(i).before(
                                        '<tr class="group_email"><td colspan="10">' + group + '</td></tr>'
                                );
                                last = group;
                            }
                        });
                        api.column(4).visible(true);  // column 4 = item title
                    }
                    // only show email info if grouped by buyable
                    if ($('#input-group_by').val() === 'buyable') {
                        api.column(1, {page: 'current'}).data().each(function (group, i) {
                            if (last !== group) {
                                $(rows).eq(i).before(
                                        '<tr class="group_buyable"><td colspan="10">' + group + '</td></tr>'
                                );
                                last = group;
                            }
                        });
                        api.column(4).visible(false);  // column 4 = item title
                    }
                    $(this).bdajax();
                }
            });
        },

        contacts_datatable_binder: function (context) {
            var url = $('#bdaplonecontacts', context).attr('data-ajaxurl');
            var oTable;
            oTable = $('#bdaplonecontacts', context).DataTable({
                "sort": false,
                "processing": true,
                "serverSide": true,
                "ajax": {
                    "url": url,
                    "data": function (d) {
                    }
                },
                "paginationType": "full_numbers",
                "lengthMenu": [
                    [5, 10, 20],
                    [5, 10, 20]
                ],
                "displayLength": 5,
                "language": {
                    "url": "@@collective.js.datatables.translation"
                },

                "sorting": [
                    [0, "desc"]
                ]
            });
        },

        dropdown_binder: function (context) {
            var options = {
                menu: '.dropdown_items',
                trigger: '.dropdown_header'
            };
            var sel = '.change_order_salaried_dropdown';
            $(sel, context).ordersdropdownmenu(options);

            sel = '.change_order_state_dropdown';
            $(sel, context).ordersdropdownmenu(options);

            sel = '.change_booking_salaried_dropdown';
            $(sel, context).ordersdropdownmenu(options);

            sel = '.change_booking_state_dropdown';
            $(sel, context).ordersdropdownmenu(options);
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

}(jQuery, bdajax, QRCode));
