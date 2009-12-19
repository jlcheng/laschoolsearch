function _log() {
    if ( eval('typeof console') != 'undefined' ) {
        console.log.apply(this, _log.arguments);
    }
}
String.prototype.trim = function() { 
    return this.replace(/^\s+|\s+$/, '');
}
var addrTable = {};
var address = function(num, street, suffix) {
    this.num = num.trim();
    this.street = street.trim();
    this.suffix = suffix.trim();
    this.key = this.num + ':' + this.street + ':' + this.suffix;
    this.displayed = false;
}

var suffixes =  ['boulevard', 'terrace', 'street', 'avenue', 'drive', 'place', 'plaza', 'blvd', 'road', 'lane', 'ave', 'way', 'st', 'rd', 'dr', 'bl', 'av', 'pz'];
suffixes.sort(function(o1,o2) { return o2.length - o1.length });
var pat = new RegExp('(\\s|^)(\\d{2,})\\s+(.+?)\\s+('+suffixes.join('|')+')','gim');
function updateSearch(text) {
    var match = null;
    while ((match = pat.exec(text))!=null) {
        var addr = new address(match[2], match[3], match[4]);
        if ( addr.suffix != null && !(addr.key in addrTable) ) {
            addrTable[addr.key] = addr;
        }
   }

    var addrstr = '';
    for (var key in addrTable) {
        var addr = addrTable[key];
        if ( addr.displayed != true ) {
            if ( addrstr != '' ) addrstr += '|'
            addrstr += key;
        }
    }
    if ( addrstr != '' ) {
        var successHandler = function(xml) {
            var addrs = $(xml).find('address');
            for (var i = 0; i < addrs.length; i++ ) {
                var addr = addrs[i];
                var addrKey = $(addr).attr('key');
                if (addrKey in addrTable) {
                    addrTable[addrKey].displayed = true;
                    var schoolstr = '';
                    var schools = $(addr).children('');
                	for (var j = 0; j < schools.length; j++ ) {
                    	if ( j != 0 ) { schoolstr += '<br/>' }
                    	schoolstr += $(schools[j]).attr('name');
                	}
                	dataTable.fnAddData([addrKey.replace(/:/g,' '), schoolstr]);
                }
            }
        }
        $.ajax({
            async: true,
            type: 'GET',
            url: '/fetch.do?addresses='+addrstr,
			dataType: 'xml',
            success: successHandler
        });
    }
}
var dataTable = null;
$(function() {
   $('#indicator').ajaxStart(function(){
        $(this).show();
    }).ajaxStop(function() {
        $(this).hide();
    });

    $('#messageArea').ajaxStart(function(){
        $(this).hide();
    }).ajaxError(function(event, request) {
        var responseText = request.responseText;
        var status = request.status + ' ' + request.statusText;
        $(this).html('<div>Yikes! You found a bug!</div> <a href="#">show debug info</a>?');
        var messageArea = this;
        $(this).find('a').bind('click',function(){
            $(this).parent().empty()
                .append('<strong>status:</strong> ' + status + '<br/>')
                .append('<strong>reponse:</strong>').append( $('<div></div>').text(responseText) ).append('<br/>');
        });
        $(this).show();
    });
    $().everyTime(1500, function(i) {
        var currText = $('#buffer').val();
        if ( currText != $('#prevText').val() ) {
            $('#prevText').val(currText);
            updateSearch(currText);
        }
    });
    dataTable = $('#results').dataTable( {
        sPaginationType: 'full_numbers'
    });
    updateSearch($('#buffer').val());
});