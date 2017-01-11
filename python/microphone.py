import pyaudio
import config

p = None
"""PyAudio's PortAudio interface"""

stream = None
"""PyAudio audio stream"""


def start_stream(callback):
    """Opens and returns a PyAudio stream of the default input device"""
    global p, stream
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=config.MIC_RATE,
                    input=True,
                    frames_per_buffer=config.MIC_RATE // config.FPS,
                    stream_callback=callback)


def close_stream():
    if stream is not None:
        """Closes and terminates the PyAudio stream"""
        stream.stop_stream()
        stream.close()
    if p is not None:
        p.terminate()
