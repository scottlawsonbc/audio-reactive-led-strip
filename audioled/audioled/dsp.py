from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import itertools
import numpy as np


def rollwin(signal, n_overlaps):
    frame = next(signal)
    N = len(frame)
    window = np.zeros(N * n_overlaps)
    window[-N:] = frame
    for data in signal:
        window[:-N] = window[N:]
        window[-N:] = data
        yield window


def normalize_scale(signal, past_n):
    buff = np.ones(past_n)
    for data in signal:
        buff[1:] = buff[:-1]
        buff[0] = data
        maxval = np.max(buff)
        minval = np.min(buff)
        if maxval != minval:
            yield (data - minval) / (maxval - minval)
        else:
            yield data * 0


def fir(taps, signal):
    """Generator that applies FIR filter taps to the iterable signal"""
    init = np.array(list(itertools.islice(signal, len(taps) - 1)))
    buff = np.tile(np.expand_dims(init[0], axis=-1), len(taps)).T
    # Consume the first N = (len(taps) - 1) values for initialization
    for chunk in init:
        buff = np.roll(buff, 1, axis=0)
        buff[0] = chunk
    # Yield the dot product of the buffer and taps (filtered result)
    for chunk in itertools.islice(signal, len(taps) - 1, None):
        buff = np.roll(buff, 1, axis=0)
        buff[0] = chunk
        yield buff.T.dot(taps)


def normalize_rms(signal, past_n):
    buff = np.zeros(past_n)
    for chunk in signal:
        buff[1:] = buff[:-1]
        buff[0] = np.sqrt(np.mean(np.square(chunk)))
        yield chunk / np.max(buff)


def downsample(signal, fs, fmax):
    """Downsamples signal by integer factor if fs > 2 * fmax

    Downsamples the signal output if downsampling is possible.
    Downsampling is possible when fs > 2*fmax, where 2*fmax is the Nyquist
    frequency for highest frequency of interest.

    Parameters
    ----------
    signal : generator
        Generator that yields a 1D np.array containing data samples
    fs : int
        Sampling rate of the unmodified signal
    fmax : int
        The highest frequency of interest.
        Frequencies higher than fmax may be removed during downsampling

    Returns
    -------
    ds_signal : generator
        Generator that yields chunks (np.array) containing data samples.
        Data samples are downsampled if downsampling is possible, otherwise
        the original signal generator is returned
    ds_fs : int
        The downsampled sampling rate. If downsampling is not possible
        then the original sampling rate is returned.
    """
    if fs < 2 * fmax:
        raise ValueError('Sampling frequency fs must be at least 2 * fmax')
    n = int(fs / (2 * fmax))
    if n == 1:
        # Downsampling is not possible
        return signal, fs
    else:
        # Downsample the signal generator
        ds_signal = (chunk[::n] for chunk in signal)
        ds_fs = int(fs // n)
        return ds_signal, ds_fs


def pad_zeros(signal):
    """Pad chunks with zeros until chunk length is a power of two

    Chunks of data yielded by the signal generator are padded with zeros
    until the length of the chunks are equal to the next largest power of
    two. No zeros are padded if the chunks are already a power of two.

    Every chunk yielded by the signal is assumed to have the same length.

    Parameters
    ----------
    signal : generator
        Generator that yields chunks of type np.array containing data that
        should be padded with zeros

    Returns
    -------
    signal : generator
        Generator that yields chunks of type np.array containing data
        that has been padded with zeros. The chunk length is equal to
        the next largest power of two greater than the original length.
        If the original chunk length was a power of two, then the signal
        generator is returned unchanged.
    """
    peek = next(signal)
    signal = itertools.chain([peek], signal)
    N = len(peek)
    N_zeros = int(2**np.ceil(np.log2(N))) - N
    zeros = np.zeros(N_zeros)
    return (np.r_[chunk, zeros] for chunk in signal)


def preemphasis(signal, coeff=0.97):
    """Applies a pre-emphasis filter to the given input signal"""
    return np.append(signal[0], signal[1:] - coeff * signal[:-1])


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
    """Returns an overlapping triangular filterbank"""
    if scale == 'mel':
        fmin_mel = 2595. * np.log10(1 + fmin_hz / 700.)
        fmax_mel = 2595. * np.log10(1 + fmax_hz / 700.)
        f_mel = np.linspace(fmin_mel, fmax_mel, n_filters + 2)
        f_hz = 700. * (np.exp(f_mel / 1127.) - 1.)
    elif scale == 'bark':
        fmin_bark = 6.0 * np.arcsinh(fmin_hz / 600.0)
        fmax_bark = 6.0 * np.arcsinh(fmax_hz / 600.0)
        f_bark = np.linspace(fmin_bark, fmax_bark, n_filters + 2)
        f_hz = 600.0 * np.sinh(f_bark / 6.0)
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


def warped_psd(y, bins, fs, frange, scale):
    """Returns the power spectrum mapped to a perceptual scale"""
    N = len(y)
    # Transform to frequency domain
    pow_spectrum = np.absolute(np.fft.rfft(y))**2 * (2 / N)
    # Construct triangular filter bank
    output, f = filter_bank(bins, N, fs, frange[0], frange[1], scale)
    # Apply filter bank to power spectrum
    output = np.dot(pow_spectrum, output.T)
    return output


def preprocess(audio, fs, fmax, n_overlaps):
    audio, fs = downsample(audio, fs=fs, fmax=fmax)
    audio = rollwin(audio, n_overlaps)
    audio = (x * np.hanning(len(x)) for x in audio)
    audio = (x for x in audio if np.sqrt(np.mean(np.square(x))) > 1e-5)
    audio = pad_zeros(audio)
    return audio, fs
