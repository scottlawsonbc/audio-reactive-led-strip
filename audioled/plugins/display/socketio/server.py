import sys
import threading

import socketio
import engineio
import eventlet

sio = socketio.Server()
app = socketio.WSGIApp(sio)


def read_stdin_and_emit():
    while True:
        line = sys.stdin.readline()
        sys.stdout.write(line, flush=True)

        fields = line.strip().split('\t')
        sio.emit('update', {
            'n': int(fields[0]),
            'r': float(fields[1]),
            'g': float(fields[2]),
            'b': float(fields[3]),
        })


def main():
    try:
        thread = threading.Thread(target=read_stdin_and_emit)
        thread.daemon = True
        thread.start()
        eventlet.wsgi.server(eventlet.listen(('', 5001)), app)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()


if __name__ == '__main__':
    main()
