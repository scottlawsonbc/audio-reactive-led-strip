from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
import pyaudio
import numpy as np
import config

p = None
"""PyAudio PortAudio interface"""

stream = None
"""PyAudio audio stream"""


def start_stream(callback=None):
    """Opens a PyAudio stream using the default audio input device"""
    global p
    global stream
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=config.MIC_RATE,
                    input=True,
                    frames_per_buffer=config.MIC_RATE // config.FPS,
                    stream_callback=callback)


def end_stream():
    stream.stop_stream()
    stream.close()
    p.terminate()


def decode(in_data, channels, dtype):
    """
    Convert a byte stream into a 2D numpy array with
    shape (chunk_size, channels)

    Samples are interleaved, so for a stereo stream with left channel
    of [L0, L1, L2, ...] and right channel of [R0, R1, R2, ...], the output
    is ordered as [L0, R0, L1, R1, ...]
    """
    # TODO: handle data type as parameter, convert between pyaudio/numpy types
    result = np.fromstring(in_data, dtype=dtype)
    chunk_length = len(result) // channels
    assert chunk_length == chunk_length
    result = np.reshape(result, (chunk_length, channels))
    return result


def encode(signal, dtype):
    """
    Convert a 2D numpy array into a byte stream for PyAudio

    Signal should be a numpy array with shape (chunk_size, channels)
    """
    interleaved = signal.flatten()
    # TODO: handle data type as parameter, convert between pyaudio/numpy types
    out_data = interleaved.astype(dtype).tostring()
    return out_data


if __name__ == '__main__':
    # List all audio devices
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i))
