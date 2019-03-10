import sys
import time
import random
import argparse


parser = argparse.ArgumentParser(description='White noise generator')
parser.add_argument('pixels', type=int, help='Number LED strip pixels.')
parser.add_argument('rate', type=int, default=60, help='Update rate in Hz.')


if __name__ == '__main__':
    args = parser.parse_args()

    while True:
        n = random.randint(0, args.pixels - 1)
        r = random.random()
        g = random.random()
        b = random.random()
        sys.stdout.write(f'{n}\t{r:.4f}\t{g:.4f}\t{b:.4f}\n')
        sys.stdout.flush()
        time.sleep(1.0 / args.rate)
