import sys
import wave
import argparse

import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('--loop', action='store_true')

def main():
    args = parser.parse_args()

    wav = wave.open(sys.stdin.buffer, 'rb')

    nframes = wav.getnframes()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    sampwidth = wav.getsampwidth()

    conversion = {
        1: (np.uint8, lambda x: (x / 255.0 - 0.5) * 2.0),
        2: (np.int16, lambda x: x / 32767.0),
    }

    # Convert WAV frames to np.array with np.float32 dtype.
    dtype, convertfn = conversion[sampwidth]
    frames = np.fromstring(wav.readframes(nframes), dtype=dtype)
    frames = convertfn(frames).astype(np.float32)

    # Convert stereo to mono.
    if nchannels == 2:
        frames = (frames[0::2] + frames[1::2]) / 2.0

    # Header information.
    sys.stdout.buffer.write(framerate.to_bytes(4, byteorder='big'))

    sys.stdout.buffer.write(frames.tobytes())
    if args.loop:
        while True:
            sys.stdout.buffer.write(frames.tobytes())


if __name__ == '__main__':
    main()
