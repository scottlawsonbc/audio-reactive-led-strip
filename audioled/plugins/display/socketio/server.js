var app = require('express')()
var server = require('http').Server(app)
var io = require('socket.io')(server)
var readline = require('readline')

var rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
})

// Pixel buffer size.
const N_PIXELS = 10

var buffer = []

server.listen(80)

// Called when a line is read from the standard input stream (stdin).
rl.on('line', function (line) {
    // Copy line to stdout.
    process.stdout.write(line + '\n')

    var fields = line.split("\t")
    var msg = [
        parseInt(fields[0]),
        parseFloat(fields[1]),
        parseFloat(fields[2]),
        parseFloat(fields[3])
    ]
    buffer.push(msg)
    if (buffer.length == N_PIXELS) {
        // console.log(buffer)
        io.emit('update', [...buffer])
        buffer = []
    }
})

// Exit when stdin is closed.
rl.on('close', function () {
    process.exit()
});

