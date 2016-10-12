from __future__ import print_function
from __future__ import division
import numpy as np
from scipy.interpolate import interp1d
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pylab as plt
plt.style.use('lawson')
import microphone as mic

# Number of frequency bands used for beat detection
N_subbands = 64

# FFT statistics for a few previous updates
N_history = int(1.0 * mic.FPS)
ys_historical_energy = np.zeros(shape=(N_subbands, N_history))
ys_beat_threshold = 6.0
ys_variance_threshold = 0.0

# def A_weighting(fs):
#     """Design of an A-weighting filter.
#     b, a = A_weighting(fs) designs a digital A-weighting filter for
#     sampling frequency `fs`. Usage: y = scipy.signal.lfilter(b, a, x).
#     Warning: `fs` should normally be higher than 20 kHz. For example,
#     fs = 48000 yields a class 1-compliant filter.
#     References:
#        [1] IEC/CD 1672: Electroacoustics-Sound Level Meters, Nov. 1996.
#     """
#     # Definition of analog A-weighting filter according to IEC/CD 1672.
#     f1 = 20.598997
#     f2 = 107.65265
#     f3 = 737.86223
#     f4 = 12194.217
#     A1000 = 1.9997
#     NUMs = [(2 * np.pi * f4)**2 * (10**(A1000 / 20)), 0, 0, 0, 0]
#     DENs = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4)**2],
#                       [1, 4 * np.pi * f1, (2 * np.pi * f1)**2])
#     DENs = np.polymul(np.polymul(DENs, [1, 2 * np.pi * f3]),
#                       [1, 2 * np.pi * f2])
#     # Use the bilinear transformation to get the digital filter.
#     # (Octave, MATLAB, and PyLab disagree about Fs vs 1/Fs)
#     return bilinear(NUMs, DENs, fs)


def beat_detect(ys):
    global ys_historical_energy
    # Beat energy criterion
    current_energy = ys * ys
    mean_energy = np.mean(ys_historical_energy, axis=1)
    has_beat_energy = current_energy > mean_energy * ys_beat_threshold
    ys_historical_energy = np.roll(ys_historical_energy, shift=1, axis=1)
    ys_historical_energy[:, 0] = current_energy
    # Beat variance criterion
    ys_variance = np.var(ys_historical_energy, axis=1)
    has_beat_variance = ys_variance > ys_variance_threshold
    # Combined energy + variance detection
    has_beat = has_beat_energy * has_beat_variance
    return has_beat


def fft(data):
    """Returns |fft(data)|"""
    yL, yR = np.split(np.abs(np.fft.fft(data)), 2)
    ys = np.add(yL, yR[::-1])
    xs = np.arange(mic.CHUNK / 2, dtype=float) * float(mic.RATE) / mic.CHUNK
    return xs, ys


def fft_log_partition(data, fmin=30, fmax=20000, subbands=64):
    """Returns FFT partitioned into subbands that are logarithmically spaced"""
    xs, ys = fft(data)
    xs_log = np.logspace(np.log10(fmin), np.log10(fmax), num=subbands * 32)
    f = interp1d(xs, ys)
    ys_log = f(xs_log)
    X, Y = [], []
    for i in range(0, subbands * 32, 32):
        X.append(np.mean(xs_log[i:i + 32]))
        Y.append(np.mean(ys_log[i:i + 32]))
    return np.array(X), np.array(Y)
