from __future__ import print_function
from __future__ import division
import time
import functools
import numpy as np
import config


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


def a(tau):
    """Converts time constant into the corresponding ExpFilter alpha value"""
    dT = 1.0 / config.FPS
    return 1.0 - np.exp(-dT / tau)


class ExpFilter:
    """Simple exponential filter"""

    def __init__(self, val=None, fall=0.5, rise=0.5):
        assert 0.0 < fall < 1.0, 'Invalid fall smoothing factor'
        assert 0.0 < rise <= 1.0, 'Invalid rise smoothing factor'
        self.fall = fall
        self.rise = rise
        self.value = val

    def update(self, value):
        # If no previous value exists then take the first value we are given
        if self.value is None:
            self.value = value
            return self.value

        if isinstance(self.value, (list, np.ndarray, tuple)):
            alpha = value - self.value
            alpha[alpha > 0.0] = self.rise
            alpha[alpha <= 0.0] = self.fall
        else:
            alpha = self.rise if value > self.value else self.fall

        self.value = alpha * value + (1.0 - alpha) * self.value
        if isinstance(self.value, (list, np.ndarray, tuple)):
            return np.copy(self.value)
        else:
            return self.value


def ApplyNormalization(fall, rise, realtime=False):
    """Decorator that applies peak normalization"""
    def normalization_decorator(func):
        if realtime:
            filt = RealTimeExpFilter(fall=fall, rise=rise)
        else:
            filt = ExpFilter(fall=fall, rise=rise)
        epsilon = np.finfo(float).eps

        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            if np.isscalar(value):
                filt.update(np.abs(value))
            else:
                filt.update(np.max(np.abs(value), axis=0))
            # Prevent division by zero
            if np.isscalar(filt.value):
                if filt.value == 0.0:
                    filt.value = epsilon
            else:
                filt.value[filt.value == 0.0] = epsilon
            value = value / filt.value
            return value
        return wrapper
    return normalization_decorator


def ApplyExpFilter(fall, rise, initial_value=None, realtime=False):
    """Decorator that applies exponential smoothing"""
    def filter_decorator(func):
        if realtime:
            filt = RealTimeExpFilter(fall=fall, rise=rise)
        else:
            filt = ExpFilter(fall=fall, rise=rise)
        filt.value = initial_value

        def wrapper(*args, **kwargs):
            filt.update(func(*args, **kwargs))
            return filt.value
        return wrapper
    return filter_decorator


def apply_filt_lr(y, filt):
    """Applies filter to the array bidirectionally

    Applies a dsp.ExpFilter to the array in both directions.
    Applying a bidirectional filter removes the phase lag.

    Parameters
    ==========
    y: np.array
        Array to apply the filter to. This is not modified.
    filt: dsp.ExpFilter
        Filter to apply to the array

    Returns
    =======
    out: np.array
        Returns a new array which is the combined result of the left and
        right applications of the dsp.ExpFilter
    """
    if np.isnan(y).any():
        raise ValueError('Cannot operate on array containing NaN value(s)')
    L = np.zeros_like(y)
    R = np.zeros_like(y)
    # Apply filter moving rightwards
    filt.value = y[0]
    for i in range(len(y)):
        R[i] = filt.update(y[i])
    filt.value = y[-1]
    # Apply filter moving leftwards
    for i in range(len(y) - 1, 0, -1):
        L[i] = filt.update(y[i])
    # Combine results
    return (L**2.0 + R**2.0)**0.5
    # return (L + R) / 2.0


def preemphasis(signal, coeff=0.97):
    """Applies a pre-emphasis filter to the given input signal"""
    return np.append(signal[0], signal[1:] - coeff * signal[:-1])


def periodic_corr(x, y):
    """Periodic correlation, implemented using the FFT.

    x and y must be real sequences with the same length.
    """
    return np.fft.ifft(np.fft.fft(x) * np.fft.fft(y).conj()).real


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
def filter_bank(n_filters, n_fft, fs, fmin_hz, fmax_hz, scale):
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
    filters = np.zeros((n_filters, n_fft // 2 + 1))
    for m in range(1, n_filters + 1):
        f_m_minus = int(bins[m - 1])   # left
        f_m = int(bins[m])             # center
        f_m_plus = int(bins[m + 1])    # right
        for k in range(f_m_minus, f_m):
            filters[m - 1, k] = (k - bins[m - 1]) / (bins[m] - bins[m - 1])
        for k in range(f_m, f_m_plus):
            filters[m - 1, k] = (bins[m + 1] - k) / (bins[m + 1] - bins[m])
    return filters, f_hz[1:-1]




if __name__ == '__main__':
    import matplotlib.pylab as plt
    config.FPS = 100

    def a(tau, dT=1):
        return 1.0 - np.exp(-dT / tau)

    def foo(samples, lp):
        # lp = ExpFilter(rise=a(0.1), fall=a(3))
        x = np.linspace(0, 10, samples)
        y = (np.sin(3.0 * x) ** 4.0 + np.sin(2.0 * x) ** 2.0) / 2.0
        z = apply_filt_lr(y, lp)
        return x, y, z
    
    a1 = 1.0 - np.exp(-256 / (3 * 256.0))
    a2 = 1.0 - np.exp(-256 / (3 * 1024.0))

    lp = ExpFilter(rise=a1, fall=a1)
    x1, y1, z1 = foo(256, lp)
    lp = ExpFilter(rise=a2, fall=a2)
    x2, y2, z2 = foo(1024, lp)

    plt.plot(x1, z1, label='y1', linewidth=3)
    plt.plot(x2, z2, label='y2', linewidth=3)
    plt.legend().draggable()
    plt.show()

