import itertools

import numpy as np

from scipy.ndimage.filters import gaussian_filter1d

import dsp


def melbins(chunks, filterbank, nbins):
    chunk = next(chunks)
    N = len(chunk)

    npad = 2**int(np.ceil(np.log2(N))) - N
    window = np.hamming(N)
    melgain = dsp.ExpFilter(np.tile(0.1, nbins).astype(np.float32), decay=0.01, rise=0.99)
    lowpass = dsp.ExpFilter(np.tile(0.1, nbins).astype(np.float32), decay=0.50, rise=0.99)

    for chunk in itertools.chain([chunk], chunks):
        # Time domain.
        chunk = chunk * window
        chunk = np.pad(chunk, (0, npad), mode='constant')
        # Frequency domain.
        freqbins = np.abs(np.fft.rfft(chunk)[:N // 2])
        freqbins = np.atleast_2d(freqbins).T * filterbank
        freqbins = np.sum(freqbins, axis=0)
        freqbins *= freqbins
        melgain.update(np.max(gaussian_filter1d(freqbins, sigma=1.0)))
        freqbins /= melgain.value
        freqbins = lowpass.update(freqbins)
        yield freqbins


def yield_chunks(nbytes, buffer):
    while True:
        frames = buffer.read(nbytes)
        if len(frames) != nbytes:
            return
        yield np.frombuffer(frames, dtype=np.float32)
