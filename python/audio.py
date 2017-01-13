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
    """Convert byte stream into 2D np.array with shape (chunk_length, channels)

    Samples are interleaved, so for a stereo stream with left channel
    of [L0, L1, L2, ...] and right channel of [R0, R1, R2, ...], the output
    is ordered as [L0, R0, L1, R1, ...]

    Parameters
    ----------
    in_data: str list
        Audio frames read from the PyAudio stream
    channels: int
        number of audio channels (mono = 1, stereo = 2)
    dtype: np.dtype
        Audio encoding dtype. For example, use np.int16 or np.float32 to
        indicate that audio is encoded as integer or float type.

    Returns
    -------
    result: np.ndarray
        Array with shape (chunk_length, channels).
        Each row contains one audio frame with columns containing the data
        for each respective channel.
    """
    result = np.fromstring(in_data, dtype=dtype)
    chunk_length = len(result) // channels
    assert chunk_length == chunk_length
    result = np.reshape(result, (chunk_length, channels))
    return result


def encode(signal, dtype):
    """Converts a 2D np.array into a PyAudio compatible byte stream

    Parameters
    ----------
    signal: np.ndarray
        2D numpy array with rows containing audio frames and the columns
        containing the data for each channel.
    dtype: np.dtype
        Datatype to use for encoding the audio data into a byte stream.
        Common data types are np.int16 and np.float32.

    Returns
    -------
    out_data: str list
        PyAudio compatible byte stream containing the audio data
    """
    interleaved = signal.flatten()
    out_data = interleaved.astype(dtype).tostring()
    return out_data


if __name__ == '__main__':
    # List all audio devices
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i))
