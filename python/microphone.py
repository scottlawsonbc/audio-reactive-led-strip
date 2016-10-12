import pyaudio

RATE = 44100
FPS = 40
CHUNK = int(RATE / FPS)


def start_stream(callback):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    while True:
        callback(stream)
    stream.stop_stream()
    stream.close()
    p.terminate()
