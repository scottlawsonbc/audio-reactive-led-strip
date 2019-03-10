import time

import numpy as np


class RealTimeExpFilter:
    """Exponential filter that references time.time()
    """

    def __init__(self, val=None, fall=0.5, rise=0.5):
        self.fall = fall
        self.rise = rise
        self.value = val
        self.t_prev = None

    def update(self, value, t=None):
        t = time.time() if t is None else t
        # Initialize value if none was given
        if self.value is None:
            self.value = value
            self.t_prev = t
            return self.value
        # Set a reference point in time
        elif self.t_prev is None:
            self.t_prev = t
            return self.value

        # Calculate elapsed since last update
        dt = t - self.t_prev
        self.t_prev += dt

        def a(tau):
            return 1.0 - np.exp(-dt / tau) if tau else 1.0

        if isinstance(self.value, (list, np.ndarray, tuple)):
            alpha = value - self.value
            alpha[alpha > 0.0] = a(self.rise)
            alpha[alpha <= 0.0] = a(self.fall)
        else:
            alpha = a(self.rise) if value > self.value else a(self.fall)

        self.value += alpha * (value - self.value)

        if isinstance(self.value, (list, np.ndarray, tuple)):
            return np.copy(self.value)
        else:
            return self.value


class ExpFilter:
    """Simple exponential smoothing filter"""
    def __init__(self, val=0.0, decay=0.5, rise=0.5):
        """Small rise / decay factors = more smoothing"""
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
        return self.value


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
def _normalized_linspace(size):
    return np.linspace(0, 1, size)


def stretch(y, new_length):
    """Intelligently resizes the array by linearly interpolating the values

    Parameters
    ----------
    y : np.array
        Array that should be resized

    new_length : int
        The length of the new interpolated array

    Returns
    -------
    z : np.array
        New array with length of new_length that contains the interpolated
        values of y.
    """
    if len(y) == new_length:
        return y
    x_old = _normalized_linspace(len(y))
    x_new = _normalized_linspace(new_length)
    z = np.interp(x_new, x_old, y)
    return z


# def rfft(data, window=None):
#     window = 1.0 if window is None else window(len(data))
#     ys = np.abs(np.fft.rfft(data * window))
#     xs = np.fft.rfftfreq(len(data), 1.0 / config.MIC_SAMPLE_FREQ_HZ)
#     return xs, ys


# def fft(data, window=None):
#     window = 1.0 if window is None else window(len(data))
#     ys = np.fft.fft(data * window)
#     xs = np.fft.fftfreq(len(data), 1.0 / config.MIC_SAMPLE_FREQ_HZ)
#     return xs, ys


# def mel_filterbank(samplerate, updaterate, nbins, fmin, fmax):
#     samples = samplerate // (2 * updaterate)
#     y, (_, x) = melbank.compute_melmat(num_mel_bands=nbins,
#                                        freq_min=fmin,
#                                        freq_max=fmax,
#                                        num_fft_bands=samples,
#                                        sample_rate=samplerate)
#     return x, y

# # def create_mel_bank():
# #     global samples, mel_y, mel_x
# #     samples = int(config.MIC_SAMPLE_FREQ_HZ / (2.0 * config.MIC_UPDATE_RATE_HZ))
# #     mel_y, (_, mel_x) = melbank.compute_melmat(num_mel_bands=config.LED_FFT_BINS,
# #                                                freq_min=config.MIC_MIN_FREQ_HZ,
# #                                                freq_max=config.MIC_MAX_FREQ_HZ,
# #                                                num_fft_bands=samples,
# #                                                sample_rate=config.MIC_SAMPLE_FREQ_HZ)
# # samples = None
# # mel_y = None
# # mel_x = None
# # create_mel_bank()
