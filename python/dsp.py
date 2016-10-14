from __future__ import print_function
from __future__ import division
import numpy as np
from scipy.interpolate import interp1d
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pylab as plt
plt.style.use('lawson')
import microphone as mic
import config

# FFT statistics for a few previous updates
_ys_historical_energy = np.zeros(shape=(config.N_SUBBANDS, config.N_HISTORY))


def beat_detect(ys):
    global _ys_historical_energy
    # Beat energy criterion
    current_energy = ys * ys
    mean_energy = np.mean(_ys_historical_energy, axis=1)
    has_beat_energy = current_energy > mean_energy * config.ENERGY_THRESHOLD
    _ys_historical_energy = np.roll(_ys_historical_energy, shift=1, axis=1)
    _ys_historical_energy[:, 0] = current_energy
    # Beat variance criterion
    ys_variance = np.var(_ys_historical_energy, axis=1)
    has_beat_variance = ys_variance > config.VARIANCE_THRESHOLD
    # Combined energy + variance detection
    has_beat = has_beat_energy * has_beat_variance
    return has_beat


def fft(data):
    """Returns |fft(data)|"""
    yL, yR = np.split(np.abs(np.fft.fft(data)), 2)
    ys = np.add(yL, yR[::-1])
    xs = np.arange(int(config.MIC_RATE / config.FPS) / 2, dtype=float)
    xs *= float(config.MIC_RATE) / int(config.MIC_RATE / config.FPS)
    return xs, ys


# def fft(data):
#     """Returns |fft(data)|"""
#     yL, yR = np.split(np.abs(np.fft.fft(data)), 2)
#     ys = np.add(yL, yR[::-1])
#     xs = np.arange(mic.CHUNK / 2, dtype=float) * float(mic.RATE) / mic.CHUNK
#     return xs, ys


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
