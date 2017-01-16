"""Feature extraction and statistical information"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
import numpy as np
import config
import dsp



def zero_crossing_rate(audio):
    """Returns the number of zero crossings in the array"""
    zcr = ((audio[:-1] * audio[1:]) < 0).sum() / len(audio)
    return zcr


@dsp.ApplyNormalization(fall=0.5, rise=1e-4, realtime=True)
def auto_spectrum(y, scale='bark'):
    """Cyclic autocorrelation spectrum with perceptual scale"""
    N = len(y)
    # Pre-emphasis filter to amplify high frequencies
    y = dsp.preemphasis(y, coeff=0.5)
    # Apply Hamming window to reduce spectral leakage
    y = y * np.hamming(N)
    # Transform to frequency domain
    # mag_spectrum = np.absolute(np.fft.rfft(y))
    mag_spectrum = np.absolute(np.real(np.fft.fft(y) * np.fft.fft(y).conj()))
    pow_spectrum = (mag_spectrum) / N
    # Construct Mel-scale triangular filter bank
    n_filters = config.N_FFT_BINS
    fs = config.MIC_RATE
    fmin_hz = config.MIN_FREQ
    fmax_hz = config.MAX_FREQ
    bins = 2 * (N - 1)
    output, f = dsp.filter_bank(n_filters, bins, fs, fmin_hz, fmax_hz, scale)
    # Apply filter bank to power spectrum
    output = np.dot(pow_spectrum, output.T)
    return output


@dsp.ApplyNormalization(fall=0.5, rise=1e-4, realtime=True)
def perceptual_spectrum(y, scale='bark'):
    N = len(y)
    # Pre-emphasis filter to amplify high frequencies
    # y = dsp.preemphasis(y, coeff=0.5)
    # Apply Hamming window to reduce spectral leakage
    y = y * np.hamming(N)
    # Transform to frequency domain
    mag_spectrum = np.absolute(np.fft.rfft(y))
    pow_spectrum = (mag_spectrum**2.0) / N
    # Construct Mel-scale triangular filter bank
    n_filters = config.N_FFT_BINS
    fs = config.MIC_RATE
    fmin_hz = config.MIN_FREQ
    fmax_hz = config.MAX_FREQ
    output, f = dsp.filter_bank(n_filters, N, fs, fmin_hz, fmax_hz, scale)
    # Apply filter bank to power spectrum
    output = np.dot(pow_spectrum, output.T)
    return output


def fft_power_spectrum(time_samples):
    mag_spectrum = np.absolute(np.fft.rfft(time_samples))
    pow_spectrum = (mag_spectrum**2.0) / len(time_samples)
    return pow_spectrum


@dsp.ApplyExpFilter(fall=5, rise=5, realtime=True)
def spectral_rolloff(power_spectrum, percentile=0.95):
    """
    Determine the spectral rolloff, i.e. the frequency below which 85%
    of the spectrum's energy is located
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
    # return rolloffIndex, frequency
    return frequency
