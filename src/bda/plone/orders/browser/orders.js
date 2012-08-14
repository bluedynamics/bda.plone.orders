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
        $("#bdaploneorders tfoot input").keyup(function() {
            /* Filter on the column (the index) of this element */
            oTable.fnFilter(this.value,
                            $("#bdaploneorders tfoot input").index(this));
        });
        $("#bdaploneorders tfoot input").each(function(i) {
            asInitVals[i] = this.value;
        });
        $("#bdaploneorders tfoot input").focus(function() {
            if (this.className == "search_init") {
                this.className = "";
                this.value = "";
            }
        });
        $("#bdaploneorders tfoot input").blur(function(i) {
            if (this.value == "") {
                this.className = "search_init";
                var idx = $("#bdaploneorders tfoot input").index(this);
                this.value = asInitVals[idx];
            }
        });
    });

})(jQuery);