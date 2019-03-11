import sys
import random
import argparse

import numpy as np

parser = argparse.ArgumentParser(description='White noise generator.')
parser.add_argument('--rate', default=44100, help='Sampling frequency (Hz).')
parser.add_argument('--chunk', default=256, help='Buffer chunk size.')


def main():
    args = parser.parse_args()

    # First four bytes must be the sampling frequency in Hertz.
    sys.stdout.buffer.write(args.rate.to_bytes(4, byteorder='big'))

    while True:
        samples = np.random.random_sample(size=args.chunk).astype(np.float32)
        samples = 2.0 * (samples - 0.5)
        sys.stdout.buffer.write(samples.tobytes())


if __name__ == '__main__':
    main()
