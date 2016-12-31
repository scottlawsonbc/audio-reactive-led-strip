from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
import socket
import numpy as np
import config

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_gamma = np.load(config.GAMMA_TABLE_PATH)
_prev_pixels = np.tile(253, (3, config.N_PIXELS))

pixels = np.tile(1, (3, config.N_PIXELS))
"""Array containing the pixel values for the LED strip"""


def update():
    global pixels, _prev_pixels
    pixels = np.clip(pixels, 0, 255).astype(int)
    m = ''
    p = _gamma[pixels] if config.GAMMA_CORRECTION else np.copy(pixels)
    for i in range(config.N_PIXELS):
        # Ignore pixels if they haven't changed (saves bandwidth)
        if np.array_equal(p[:, i], _prev_pixels[:, i]):
            continue
        m += chr(i) + chr(p[0][i]) + chr(p[1][i]) + chr(p[2][i])
    _prev_pixels = np.copy(p)
    _sock.sendto(m.encode(), (config.UDP_IP, config.UDP_PORT))


# Execute this file to run a LED strand test
# If everything is working, you should see a red, green, and blue pixel scroll
# across the LED strip continously
if __name__ == '__main__':
    import time
    # Turn all pixels off
    pixels *= 0
    pixels[0, 0] = 255 # Set 1st pixel red
    pixels[1, 1] = 255 # Set 2nd pixel green
    pixels[2, 2] = 255 # Set 3rd pixel blue
    print('Starting LED strand test')
    while True:
        pixels = np.roll(pixels, 1, axis=1)
        update()
        time.sleep(0.2)

