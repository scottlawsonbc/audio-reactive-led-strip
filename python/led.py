from __future__ import print_function
import time
import socket
import numpy as np

# Nonlinear brightness correction
lookup_table = np.load('lookup_table.npy')
N_pixels = 240
m = None

# Socket communication settings
UDP_IP = "192.168.0.100"
UDP_PORT = 7777
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def set_all(R, G, B):
    for i in range(N_pixels):
        set_pixel(i, R, G, B)
    update_pixels()


def set_from_array(x):
    dt = 2.0 * np.pi / N_pixels
    t = time.time() * 1.5
    def r(t): return (np.sin(t + 0.0) + 1.0) * 1.0 / 2.0
    def g(t): return (np.sin(t + (2.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
    def b(t): return (np.sin(t + (4.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
    for n in range(N_pixels):
        set_pixel(N=n,
                  R=r(n * dt + t) * x[n],
                  G=g(n * dt + t) * x[n],
                  B=b(n * dt + t) * x[n],
                  nonlinear_correction=True)
    update_pixels()


def set_pixel(N, R, G, B, nonlinear_correction=True):
    global m
    r = int(min(max(R, 0), 255))
    g = int(min(max(G, 0), 255))
    b = int(min(max(B, 0), 255))
    if nonlinear_correction:
        r = lookup_table[r]
        g = lookup_table[g]
        b = lookup_table[b]
    if m is None:
        m = chr(N) + chr(r) + chr(g) + chr(b)
    else:
        m += chr(N) + chr(r) + chr(g) + chr(b)


def update_pixels():
    global m
    sock.sendto(m, (UDP_IP, UDP_PORT))
    m = None


def rainbow(brightness=255.0, speed=1.0, fps=10):
    offset = 132
    dt = 2.0 * np.pi / N_pixels
    def r(t): return (np.sin(t + 0.0) + 1.0) * brightness / 2.0 + offset
    def g(t): return (np.sin(t + (2.0 / 3.0) * np.pi) + 1.0) * brightness / 2.0 + offset
    def b(t): return (np.sin(t + (4.0 / 3.0) * np.pi) + 1.0) * brightness / 2.0 + offset
    while True:
        t = time.time() * speed
        for n in range(N_pixels):
            T = t + n * dt
            set_pixel(N=n, R=r(T), G=g(T), B=b(T))
        update_pixels()
        time.sleep(1.0 / fps)


if __name__ == '__main__':
    for i in range(N_pixels):
        set_all(0, 0, 0)
    # rainbow(speed=0.025, fps=40, brightness=0)
