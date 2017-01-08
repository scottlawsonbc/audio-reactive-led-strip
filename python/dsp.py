from __future__ import print_function
from __future__ import division
import numpy as np
import config


class ExpFilter:
    """Exponential filter"""
    def __init__(self, val=0.0, decay=0.5, rise=0.5):
        assert 0.0 < decay < 1.0, 'Invalid decay smoothing factor'
        assert 0.0 < rise < 1.0, 'Invalid rise smoothing factor'
        self.decay = decay
        self.rise = rise
        self.value = val

    def update(self, value):
        if isinstance(self.value, (list, np.ndarray, tuple)):
            alpha = value - self.value
            alpha[alpha > 0.0] = self.rise
            alpha[alpha <= 0.0] = self.decay
        else:
            alpha = self.rise if value > self.value else self.decay
        self.value = alpha * value + (1.0 - alpha) * self.value
        return np.copy(self.value)


def preemphasis(signal, coeff=0.97):
    """Applies a pre-emphasis filter to the given input signal"""
    return np.append(signal[0], signal[1:] - coeff * signal[:-1])


def _hz_to_mel(f):
    """Given frequency f in Hz, returns corresponding frequency in mels"""
    return 2595. * np.log10(1 + f / 700.)


def _mel_to_hz(m):
    """Given frequency m in mels, returns corresponding frequency in Hz"""
    return 700. * (np.exp(m / 1127.) - 1.)


def _hz_to_bark(f):
    """Given frequency f in Hz, returns corresponding frequency in barks"""
    return 6.0 * np.arcsinh(f / 600.0)


def _bark_to_hz(z):
    """Given frequency z in barks, returns corresponding frequency in Hz"""
    return 600.0 * np.sinh(z / 6.0)


def memoize(function):
    """Provides a decorator for memoizing functions"""
    from functools import wraps
    memo = {}

    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


@memoize
def construct_filter_bank(n_filters, n_fft, fs, fmin_hz, fmax_hz, scale='mel'):
    if scale == 'mel':
        fmin_mel = _hz_to_mel(fmin_hz)
        fmax_mel = _hz_to_mel(fmax_hz)
        f_mel = np.linspace(fmin_mel, fmax_mel, n_filters + 2)
        f_hz = _mel_to_hz(f_mel)
    elif scale == 'bark':
        fmin_bark = _hz_to_bark(fmin_hz)
        fmax_bark = _hz_to_bark(fmax_hz)
        f_bark = np.linspace(fmin_bark, fmax_bark, n_filters + 2)
        f_hz = _bark_to_hz(f_bark)
    # Convert from Hz points to FFT bin number
    bins = np.floor((n_fft + 1.) * f_hz / fs)
    # Construct the filter bank
    filter_bank = np.zeros((n_filters, n_fft // 2 + 1))
    for m in range(1, n_filters + 1):
        f_m_minus = int(bins[m - 1])   # left
        f_m = int(bins[m])             # center
        f_m_plus = int(bins[m + 1])    # right
        for k in range(f_m_minus, f_m):
            filter_bank[m - 1, k] = (k - bins[m - 1]) / (bins[m] - bins[m - 1])
        for k in range(f_m, f_m_plus):
            filter_bank[m - 1, k] = (bins[m + 1] - k) / (bins[m + 1] - bins[m])
    return filter_bank, f_hz[1:-1]


def extract_features(y):
    N = len(y)
    # Pre-emphasis filter to amplify high frequencies
    #y = preemphasis(y, coeff=0.7)
    # Apply Hamming window to reduce spectral leakage
    y *= np.hamming(N)
    # Transform to frequency domain
    mag_spectrum = np.absolute(np.fft.rfft(y))
    pow_spectrum = (mag_spectrum**2.0) / N
    # Construct Mel-scale triangular filter bank
    n_filters = config.N_FFT_BINS
    fs = config.MIC_RATE
    fmin_hz = config.MIN_FREQUENCY
    fmax_hz = config.MAX_FREQUENCY
    output, f = construct_filter_bank(n_filters, N, fs, fmin_hz, fmax_hz)
    # Apply filter bank to power spectrum
    output = np.dot(pow_spectrum, output.T)
    return output, f
