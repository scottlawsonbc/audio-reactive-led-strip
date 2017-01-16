import pyaudio
import config
import sys


channelcount = None
"""Number of channels in the audio streams"""

def start_stream(callback):
    p = pyaudio.PyAudio()
    device_info = p.get_device_info_by_index(config.DEVICE_INDEX)
    if (device_info["maxOutputChannels"] < device_info["maxInputChannels"]):
        channelcount = device_info["maxInputChannels"]
    else:
        channelcount = device_info["maxOutputChannels"]
    stream = p.open(format=pyaudio.paInt16,
                    channels=channelcount,
                    rate=config.MIC_RATE,
                    input=True,
                    frames_per_buffer=int(config.MIC_RATE
                                          / config.FPS),
                    input_device_index=config.DEVICE_INDEX,
                    as_loopback=config.USE_LOOPBACK)
    while True:
        callback(stream)
    stream.stop_stream()
    stream.close()
    p.terminate()
