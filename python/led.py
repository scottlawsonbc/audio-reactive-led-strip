from __future__ import print_function
import time
import socket
import numpy as np
import config

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_gamma = np.load('gamma_table.npy')
_prev_pixels = np.tile(0, (config.N_PIXELS, 3))

pixels = np.tile(0, (config.N_PIXELS, 3))
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
    _prev_pixels = pixels
    _sock.sendto(m, (config.UDP_IP, config.UDP_PORT))



# def set_all(R, G, B):
#     for i in range(config.N_PIXELS):
#         set_pixel(i, R, G, B)
#     update_pixels()


# def autocolor(x, speed=1.0):
#     dt = 2.0 * np.pi / config.N_PIXELS
#     t = time.time() * speed
#     def r(t): return (np.sin(t + 0.0) + 1.0) * 1.0 / 2.0
#     def g(t): return (np.sin(t + (2.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
#     def b(t): return (np.sin(t + (4.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
#     for n in range(config.N_PIXELS):
#         set_pixel(N=n,
#                   R=r(n * dt + t) * x[n],
#                   G=g(n * dt + t) * x[n],
#                   B=b(n * dt + t) * x[n],
#                   gamma_correction=True)
#     update_pixels()


# def set_pixel(N, R, G, B, gamma_correction=True):
#     global _m
#     r = int(min(max(R, 0), 255))
#     g = int(min(max(G, 0), 255))
#     b = int(min(max(B, 0), 255))
#     if gamma_correction:
#         r = _gamma_table[r]
#         g = _gamma_table[g]
#         b = _gamma_table[b]
#     if _m is None:
#         _m = chr(N) + chr(r) + chr(g) + chr(b)
#     else:
#         _m += chr(N) + chr(r) + chr(g) + chr(b)


# def update_pixels():
#     global _m
#     _sock.sendto(_m, (config.UDP_IP, config.UDP_PORT))
#     _m = None


# def rainbow(brightness=255.0, speed=1.0, fps=10):
#     offset = 132
#     dt = 2.0 * np.pi / config.N_PIXELS
#     def r(t): return (np.sin(t + 0.0) + 1.0) * brightness / 2.0 + offset
#     def g(t): return (np.sin(t + (2.0 / 3.0) * np.pi) + 1.0) * brightness / 2.0 + offset
#     def b(t): return (np.sin(t + (4.0 / 3.0) * np.pi) + 1.0) * brightness / 2.0 + offset
#     while True:
#         t = time.time() * speed
#         for n in range(config.N_PIXELS):
#             T = t + n * dt
#             set_pixel(N=n, R=r(T), G=g(T), B=b(T))
#         update_pixels()
#         time.sleep(1.0 / fps)


if __name__ == '__main__':
    while True:
        update()
        #set_all(0, 0, 0)
    # rainbow(speed=0.025, fps=40, brightness=0)
