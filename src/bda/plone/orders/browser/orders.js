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
                "sSearch": "Alles durchsuchen:"
            }
        });
    });

})(jQuery);