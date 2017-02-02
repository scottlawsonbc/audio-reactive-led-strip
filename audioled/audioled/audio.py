from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import numpy as np
import pyaudio


def default_input_stream():
    """Opens a PyAudio stream using the default audio input device"""
    p = pyaudio.PyAudio()
    defaults = p.get_default_host_api_info()
    default_index = defaults['defaultInputDevice']
    default_input = p.get_device_info_by_index(default_index)

    if default_input['maxInputChannels'] == 0:
        err = 'Your default audio input device cannot be opened. '
        err += 'Change your system default audio input device and try again. '
        err += 'Device info:\n{}\n{}'.format(defaults, default_input)
        raise OSError(err)

    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=int(default_input['defaultSampleRate']),
                        input=True,
                        frames_per_buffer=0)
    except OSError as e:
        err = 'Error occurred while attempting to open audio device. '
        err += 'Check your operating system\'s audio device configuration. '
        err += 'Audio device information: \n'
        err += str(default_input)
        print(err)
        raise e
    return stream, int(default_input['defaultSampleRate'])


def stream_audio(chunk_rate=60, exception_on_overflow=False):
    stream, fs = default_input_stream()
    chunk_length = int(fs // chunk_rate)

    def audio_chunks():
        audio_stream = stream
        audio_fs = fs
        while True:
            try:
                chunk = audio_stream.read(chunk_length)
            except OSError as e:
                if e.errno == pyaudio.paInputOverflowed:
                    msg = 'The audio input buffer has overflowed. '
                    msg = 'An occasional overflow is normal. '
                    msg += 'Try lowering the FPS if this happens often.'
                    print(msg)
                    if exception_on_overflow:
                        raise e
                    else:
                        audio_stream, audio_fs = default_input_stream()
                        chunk = stream.read(chunk_length)
            chunk = np.fromstring(chunk, np.float32)
            chunk = chunk.astype(np.float64)
            yield chunk
    return audio_chunks(), fs

if __name__ == '__main__':
    # List all audio devices
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i))
