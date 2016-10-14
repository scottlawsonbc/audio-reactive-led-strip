import pyaudio
import config

CHUNK = int(config.MIC_RATE / config.FPS)

def start_stream(callback):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=config.MIC_RATE,
                    input=True,
                    frames_per_buffer=int(config.MIC_RATE / config.FPS))
    while True:
        callback(stream)
    stream.stop_stream()
    stream.close()
    p.terminate()
