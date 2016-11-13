from __future__ import print_function
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
    pixels = np.clip(pixels, 0, 255)
    m = ''
    p = _gamma[pixels] if config.GAMMA_CORRECTION else np.copy(pixels)
    for i in range(config.N_PIXELS):
        # Ignore pixels if they haven't changed (saves bandwidth)
        if np.array_equal(p[:, i], _prev_pixels[:, i]):
            continue
        m += chr(i) + chr(p[0][i]) + chr(p[1][i]) + chr(p[2][i])
    _prev_pixels = np.copy(p)
    _sock.sendto(m, (config.UDP_IP, config.UDP_PORT))


if __name__ == '__main__':
    pixels = pixels * 0
    pixels = pixels
    update()

