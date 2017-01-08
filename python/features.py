"""Feature extraction and statistical information"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
import numpy as np
import config
import dsp
from dsp import a


#@dsp.ApplyExpFilter(decay=a(0.01), rise=a(0.01))
@dsp.ApplyNormalization(decay=a(3))
def zero_crossing_rate(audio):
    """Returns the number of zero crossings in the array"""
    zcr = ((audio[:-1] * audio[1:]) < 0).sum() / len(audio)
    return zcr


@dsp.ApplyNormalization(decay=a(3))
def mel_spectrum(y):
    N = len(y)
    # Pre-emphasis filter to amplify high frequencies
    #y = dsp.preemphasis(y, coeff=0.8)
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
    output, f = dsp.filter_bank(n_filters, N, fs, fmin_hz, fmax_hz, 'mel')
    # Apply filter bank to power spectrum
    output = np.dot(pow_spectrum, output.T)
    return output


