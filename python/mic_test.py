import numpy
import pyaudio
import wave

FORMAT = pyaudio.paInt16
CHANNELS = 1
#RATE = 44100
RATE = 48000
INPUT_DEVICE_INDEX = 6
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "/home/pi/e//audio/test-rpi.wav"
CHUNK=1024

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open input stream, 16-bit mono at 48000 Hz
# On my system, device 6 is a USB microphone
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    frames_per_buffer=CHUNK,
    input_device_index=INPUT_DEVICE_INDEX,
    input=True)

print('Recording')
frames = []

print(f'Recording cycles {int(RATE / CHUNK * RECORD_SECONDS)}')

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    try:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    except IOError:
        continue

print('Done recording')

stream.stop_stream()
stream.close()
audio.terminate()

waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(frames))
waveFile.close()
