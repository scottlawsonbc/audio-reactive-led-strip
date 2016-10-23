from __future__ import print_function
import socket
import numpy as np
import config

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_gamma = np.load('gamma_table.npy')
_prev_pixels = np.tile(0, (config.N_PIXELS, 3))

pixels = np.tile(1, (config.N_PIXELS, 3))
"""Array containing the pixel values for the LED strip"""


def update():
    global pixels, _prev_pixels
    pixels = np.clip(pixels, 0, 255)
    m = ''
    for i in range(config.N_PIXELS):
        # Ignore pixels if they haven't changed (saves bandwidth)
        if np.array_equal(pixels[i], _prev_pixels[i]):
            continue
        r = _gamma[pixels[i][0]] if config.GAMMA_CORRECTION else pixels[i][0]
        g = _gamma[pixels[i][1]] if config.GAMMA_CORRECTION else pixels[i][1]
        b = _gamma[pixels[i][2]] if config.GAMMA_CORRECTION else pixels[i][2]
        m += chr(i) + chr(r) + chr(g) + chr(b)
    _prev_pixels = np.copy(pixels)
    _sock.sendto(m, (config.UDP_IP, config.UDP_PORT))


if __name__ == '__main__':

    pixels += 0.0
    update()
