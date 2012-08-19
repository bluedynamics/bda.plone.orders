(function($) {
    
    var asInitVals = new Array();
    
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
            "aaSorting": [[1, "asc"]]
        });
    });

})(jQuery);