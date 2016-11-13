from __future__ import print_function
import numpy as np
from scipy.interpolate import interp1d
import config
import melbank


class ExpFilter:
    """Simple exponential smoothing filter"""
    def __init__(self, val=0.0, alpha_decay=0.5, alpha_rise=0.5):
        """Small rise / decay factors = more smoothing"""
        assert 0.0 < alpha_decay < 1.0, 'Invalid decay smoothing factor'
        assert 0.0 < alpha_rise < 1.0, 'Invalid rise smoothing factor'
        self.alpha_decay = alpha_decay
        self.alpha_rise = alpha_rise
        self.value = val

    def update(self, value):
        if not isinstance(self.value, (int, long, float)):
            alpha = value - self.value
            alpha[alpha > 0.0] = self.alpha_rise
            alpha[alpha <= 0.0] = self.alpha_decay
        else:
            alpha = self.alpha_rise if value > self.value else self.alpha_decay
        self.value = alpha * value + (1.0 - alpha) * self.value
        return self.value


def wrap_phase(phase):
    """Converts phases in the range [0, 2 pi] to [-pi, pi]"""
    return (phase + np.pi) % (2 * np.pi) - np.pi


ys_prev = None
phase_prev = None
dphase_prev = None


def onset(yt):
    """Detects onsets in the given audio time series data

    Onset detection is perfomed using an ensemble of three onset detection
    functions.

    The first onset detection function uses the rectified spectral flux (SF)
    of successive FFT data frames.
    The second onset detection function uses the normalized weighted phase
    difference (NWPD) of successive FFT data frames.
    The third is a rectified complex domain onset detection function.

    The product of these three functions forms an ensemble onset detection
    function that returns continuous valued onset detection estimates.

    Parameters
    ----------
    yt : numpy.array
        Array of time series data to perform onset detection on

    Returns
    -------
    SF : numpy.array
        Array of rectified spectral flux values
    NWPD : numpy.array
        Array of normalized weighted phase difference values
    RCD : numpy.array
        Array of rectified complex domain values

    References
    ----------
    Dixon, Simon "Onset Detection Revisted"
    """
    global ys_prev, phase_prev, dphase_prev
    xs, ys = fft(yt, window=np.hamming)
    ys = ys[(xs >= config.MIN_FREQUENCY) * (xs <= config.MAX_FREQUENCY)]
    xs = xs[(xs >= config.MIN_FREQUENCY) * (xs <= config.MAX_FREQUENCY)]
    magnitude = np.abs(ys)
    phase = np.angle(ys)
    # Special case for initialization
    if ys_prev is None:
        ys_prev = ys
        phase_prev = phase
        dphase_prev = phase
    # Rectified spectral flux
    SF = magnitude - np.abs(ys_prev)
    SF[SF < 0.0] = 0.0
    # First difference of phase
    dphase = phase - phase_prev
    # Second difference of phase
    ddphase = dphase - dphase_prev
    # Normalized weighted phase deviation
    NWPD = np.abs(ddphase) * magnitude
    # Rectified complex domain onset detection function
    RCD = np.abs(ys - ys_prev * dphase_prev)
    RCD[RCD < 0.0] = 0.0
    RCD = RCD
    # Update previous values
    ys_prev = ys
    phase_prev = phase
    dphase_prev = dphase
    # Replace NaN values with zero
    SF = np.nan_to_num(SF)
    NWPD = np.nan_to_num(NWPD)
    RCD = np.nan_to_num(RCD)
    # Convert onset detection to logarithmically spaced bins
    _, SF = log_partition(xs, SF, subbands=config.N_SUBBANDS)
    _, NWPD = log_partition(xs, NWPD, subbands=config.N_SUBBANDS)
    _, RCD = log_partition(xs, RCD, subbands=config.N_SUBBANDS)
    return SF, NWPD, RCD


def rfft(data, window=None):
    window = 1.0 if window is None else window(len(data))
    ys = np.abs(np.fft.rfft(data * window))
    xs = np.fft.rfftfreq(len(data), 1.0 / config.MIC_RATE)
    return xs, ys


def fft(data, window=None):
    window = 1.0 if window is None else window(len(data))
    ys = np.fft.fft(data * window)
    xs = np.fft.fftfreq(len(data), 1.0 / config.MIC_RATE)
    return xs, ys


def log_partition(xs, ys, subbands):
    f = interp1d(xs, ys)
    xs_log = np.logspace(np.log10(xs[0]), np.log10(xs[-1]), num=subbands * 24)
    xs_log[0] = xs[0]
    xs_log[-1] = xs[-1]
    ys_log = f(xs_log)
    X, Y = [], []
    for i in range(0, subbands * 24, 24):
        X.append(np.mean(xs_log[i:i + 24]))
        Y.append(np.mean(ys_log[i:i + 24]))
    return np.array(X), np.array(Y)




samples = int(round(config.MIC_RATE * config.N_ROLLING_HISTORY / (2.0 * config.FPS)))
mel_y, (_, mel_x) = melbank.compute_melmat(num_mel_bands=config.N_SUBBANDS,
                                           freq_min=config.MIN_FREQUENCY,
                                           freq_max=config.MAX_FREQUENCY,
                                           num_fft_bands=samples,
                                           sample_rate=config.MIC_RATE)

def create_mel_bank(n_history):
    global samples, mel_y, mel_x
    config.N_ROLLING_HISTORY = n_history
    samples = int(round(config.MIC_RATE * config.N_ROLLING_HISTORY / (2.0 * config.FPS)))
    mel_y, (_, mel_x) = melbank.compute_melmat(num_mel_bands=config.N_SUBBANDS,
                                               freq_min=config.MIN_FREQUENCY,
                                               freq_max=config.MAX_FREQUENCY,
                                               num_fft_bands=samples,
                                               sample_rate=config.MIC_RATE)
