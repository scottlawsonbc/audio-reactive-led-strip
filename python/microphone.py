import time
import numpy as np
import pyaudio
import config
from pydub import AudioSegment
from pydub.utils import make_chunks

def start_stream(callback):
    sound = AudioSegment.from_file("/home/pi/Stars_Align.mp3")

    p = pyaudio.PyAudio()
    frames_per_buffer = int(config.MIC_RATE / config.FPS)
    stream = p.open(format=pyaudio.paInt16,
                    channels=sound.channels,
                    rate=config.MIC_RATE,
                    # input=True,
                    output=True,
                    frames_per_buffer=frames_per_buffer)
    overflows = 0
    prev_ovf_time = time.time()
    while True:
        try:
            # y = np.fromstring(stream.read(frames_per_buffer, exception_on_overflow=False), dtype=np.int16)
            # y = y.astype(np.float32)
            # stream.read(stream.get_read_available(), exception_on_overflow=False)
            # callback(y)
            start = 0
            length = sound.duration_seconds
            volume = 100.0
            playchunk = sound[start * 1000.0:(start + length) * 1000.0] - (60 - (60 * (volume / 100.0)))
            millisecondchunk = 50 / 1000.0

            for chunks in make_chunks(playchunk, millisecondchunk * 1000):
                stream.write(chunks._data)
                y = np.frombuffer(chunks._data, dtype=np.int16)
                y = y.astype(np.float32)
                callback(y)
        except IOError:
            overflows += 1
            if time.time() > prev_ovf_time + 1:
                prev_ovf_time = time.time()
                print('Audio buffer has overflowed {} times'.format(overflows))
    stream.stop_stream()
    stream.close()
    p.terminate()
