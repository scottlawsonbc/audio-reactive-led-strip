from __future__ import print_function
import socket
import numpy as np
import config

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_gamma = np.load(config.GAMMA_TABLE_PATH)
_prev_pixels = np.tile(253, (config.N_PIXELS, 3))

pixels = np.tile(1, (config.N_PIXELS, 3))
"""Array containing the pixel values for the LED strip"""


def update():
    global pixels, _prev_pixels
    pixels = np.clip(pixels, 0, 255)
    m = ''
    p = _gamma[pixels] if config.GAMMA_CORRECTION else np.copy(pixels)
    for i in range(config.N_PIXELS):
        # Ignore pixels if they haven't changed (saves bandwidth)
        if np.array_equal(p[i], _prev_pixels[i]):
            continue
        m += chr(i) + chr(p[i][0]) + chr(p[i][1]) + chr(p[i][2])
    _prev_pixels = np.copy(p)
    _sock.sendto(m, (config.UDP_IP, config.UDP_PORT))


if __name__ == '__main__':
    pixels = pixels * 0
    pixels = pixels
    update()

