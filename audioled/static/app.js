
function updateForms() {
    $('.plugin').hide()
    $.each($('.plugin-select option:selected'), function(){
        var pluginId = $(this).val()
        $('#' + pluginId).show()
    });
}

function getPluginParams(plugin) {
    var nameFields = $(plugin).children().find('.field-name:visible')
    var valueFields = $(plugin).children().find('.field-value:visible')
    var params = {}
    for (var i = 0; i < nameFields.length; i++) {
        var name = nameFields[i].innerText
        var value = valueFields[i].value
        if (value != '') {
            params[name] = value
        }
    }
    return params
}

function getRequestPayload() {
    var payload = {
        jsonrpc: '2.0',
        method: 'run',
        params: {
            source: $('#source').children().find('.plugin-select').val(),
            source_params: getPluginParams('#source'),
            effect: $('#effect').children().find('.plugin-select').val(),
            effect_params: getPluginParams('#effect'),
            display: $('#display').children().find('.plugin-select').val(),
            display_params: getPluginParams('#display'),
        },
        id: 1
    }
    return payload;
}

function rpc(payload) {
    console.log(payload)
    $.ajax({
        url: 'api',
        dataType: 'json',
        contentType: 'application/json;charset=utf-8',
        type: 'POST',
        data: JSON.stringify(payload),
        success: function (msg) {
            console.log('REPLY')
            console.log(msg)
        },
        error: function (msg) {
            console.log('ERROR')
            console.log(msg)
        },
    });
}



var socket = io.connect('http://localhost');
var ledstrip = document.getElementById('ledstrip');
var N_PIXELS = 100
var pixels = []

for (var i = 0; i < N_PIXELS; i++) {
    pixel = document.createElement('div');
    pixel['background-color'] = 'black';
    pixel.className = 'pixel';
    pixels.push(pixel)
    ledstrip.appendChild(pixel);
}

socket.on('update', function (msgs) {
    for (var i = 0; i < msgs.length; i++) {
        var msg = msgs[i]
        var n = msg[0]
        var r = Math.round(msg[1] * 255)
        var g = Math.round(msg[2] * 255)
        var b = Math.round(msg[3] * 255)
        var pixel = pixels[n]
        pixel.setAttribute('style', 'background-color: rgb(' + r + ', ' + g + ', ' + b + ')')
    }
});


$(document).ready(function () {

    $('.plugin-btn').on('click', function() {
        rpc(getRequestPayload())
    });

    $('.plugin-select').on('change', function() {
        updateForms()
    });


    $('.field-value').on('change', function() {
        id = $(this).attr('id')
        localStorage.setItem(id, $(this).val())
        console.log(id + ' saved')
    });

    $.each($('.field-value'), function(){
        id = $(this).attr('id')
        $(this).val(localStorage.getItem(id))
    });


    updateForms()
})
