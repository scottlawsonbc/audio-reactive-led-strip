var socket = io.connect('http://localhost');
var ledstrip = document.getElementById('ledstrip');
var N_PIXELS = 100
var pixels = []

for (var i = 0; i < N_PIXELS; i++) {
    pixel = document.createElement('div');
    pixel.innerText += ''
    pixel['background-color'] = 'black';
    pixel.className = 'ledlight';
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
