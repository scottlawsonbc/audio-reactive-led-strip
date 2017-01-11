from __future__ import print_function
from __future__ import division
import time
import numpy as np
import config


class RealTimeExpFilter:
    """Exponential filter that works when sampling time is noisy"""

    def __init__(self, val=None, decay=0.5, rise=0.5):
        self.decay = decay
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
            return 1.0 - np.exp(-dt / tau)

        if isinstance(self.value, (list, np.ndarray, tuple)):
            alpha = value - self.value
            alpha[alpha > 0.0] = a(self.rise)
            alpha[alpha <= 0.0] = a(self.decay)
        else:
            alpha = a(self.rise) if value > self.value else a(self.decay)

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

    def __init__(self, val=None, decay=0.5, rise=0.5):
        assert 0.0 < decay < 1.0, 'Invalid decay smoothing factor'
        assert 0.0 < rise <= 1.0, 'Invalid rise smoothing factor'
        self.decay = decay
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
            alpha[alpha <= 0.0] = self.decay
        else:
            alpha = self.rise if value > self.value else self.decay

        self.value = alpha * value + (1.0 - alpha) * self.value
        if isinstance(self.value, (list, np.ndarray, tuple)):
            return np.copy(self.value)
        else:
            return self.value


def ApplyNormalization(decay, rise=1, realtime=False):
    """Decorator that applies peak normalization"""
    def normalization_decorator(function):
        if realtime:
            filt = RealTimeExpFilter(decay=decay, rise=rise)
        else:
            filt = ExpFilter(decay=decay, rise=rise)
        epsilon = np.finfo(float).eps

        def wrapper(*args, **kwargs):
            value = function(*args, **kwargs)
            filt.update(np.abs(value))
            if np.isscalar(value):
                filt.update(np.abs(value))
            else:
                filt.update(np.max(np.abs(value), axis=0))
            # Prevent division by zero
            if np.isscalar(filt.value):
                if filt.value == 0.0:
                    filt.value = epsilon
            else:
                filt.value = np.where(filt.value == 0, epsilon, filt.value)
            value /= filt.value
            return value
        return wrapper
    return normalization_decorator


def ApplyExpFilter(decay, rise, initial_value=None, realtime=False):
    """Decorator that applies exponential smoothing"""
    def filter_decorator(function):
        if realtime:
            filt = RealTimeExpFilter(decay=decay, rise=rise)
        else:
            filt = ExpFilter(decay=decay, rise=rise)
        filt.value = initial_value

        def wrapper(*args, **kwargs):
            filt.update(function(*args, **kwargs))
            return filt.value
        return wrapper
    return filter_decorator


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


def spectral_rolloff(power_spectrum, percentile=0.85):
    """
    Determine the spectral rolloff, i.e. the frequency below which 85% of the spectrum's energy
    is located
    """
    absSpectrum = power_spectrum
    spectralSum = np.sum(absSpectrum)
    rolloffSum = 0
    rolloffIndex = 0
    for i in range(0, len(power_spectrum)):
        rolloffSum = rolloffSum + absSpectrum[i]
        if rolloffSum > (percentile * spectralSum):
            rolloffIndex = i
            break
    # Convert the index into a frequency
    frequency = rolloffIndex * (config.MIC_RATE / 2.0) / len(power_spectrum)
    return rolloffIndex, frequency


if __name__ == '__main__':
    import matplotlib.pylab as plt
    config.FPS = 100

    def a(tau):
        """Converts time constant into the corresponding ExpFilter alpha value"""
        dT = 1.0 / config.FPS
        return 1.0 - np.exp(-dT / tau)

    N = 10.0 * config.FPS
    t_clean = np.linspace(0, N / config.FPS, N)
    noise = np.random.random(N) - 0.5
    noise *= t_clean[1] - t_clean[0]
    noise /= 100.0
    t_noisy = t_clean + noise

    x = np.sin(300. * 2. * np.pi * t_clean)
    y = np.sin(300. * 2. * np.pi * t_noisy)
    z = np.sin(300. * 2. * np.pi * t_noisy)

    a = ExpFilter(decay=a(0.5), rise=a(0.5))
    b = ExpFilter(decay=0.5, rise=0.5)
    c = RealTimeExpFilter(decay=0.5, rise=0.5)

    for i in range(len(y)):
        x[i] = a.update(x[i])
        y[i] = b.update(y[i])
        z[i] = c.update(z[i], t=t_noisy[i])

    plt.plot(t_clean, x, color='red')
    plt.plot(t_noisy, y, color='green')
    plt.plot(t_noisy, z, color='blue')
    plt.show()