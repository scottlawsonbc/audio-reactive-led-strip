import sys
import time
import struct
import argparse

import numpy as np

from scipy.ndimage.filters import gaussian_filter1d

import dsp
import mel
import audio


def scroll(freqbins, npixels, nbins):
    N = npixels // 2
    pixels = np.tile(1.0, (3, N))
    lowpass = dsp.ExpFilter(np.tile(0.01, nbins), decay=0.001, rise=0.99)

    for fbins in freqbins:
        fbins = fbins**2.0
        lowpass.update(fbins)
        fbins /= lowpass.value
        # Assign colors.
        r = np.max(fbins[:N//3])
        g = np.max(fbins[N//3: 2*N//3])
        b = np.max(fbins[2*N//3:])
        # Scrolling effect window.
        pixels[:, 1:] = pixels[:, :-1]
        pixels *= 0.98
        pixels = gaussian_filter1d(pixels, sigma=0.2)
        # Create new color originating at the center
        pixels[0, 0] = r
        pixels[1, 0] = g
        pixels[2, 0] = b
        # Update the LED strip
        yield np.concatenate((pixels[:, ::-1], pixels), axis=1)


def spectrum(freqbins, npixels, nbins):
    N = npixels // 2
    prevbins = np.tile(0.01, N)
    lowpass = dsp.RealTimeExpFilter(np.tile(0.01, N), fall=0.95, rise=0.01)
    r_lowpass = dsp.RealTimeExpFilter(np.tile(0.01, N), fall=0.01, rise=0.99)
    g_lowpass = dsp.RealTimeExpFilter(np.tile(0.01, N), fall=0.05, rise=0.3)
    b_lowpass = dsp.RealTimeExpFilter(np.tile(0.01, N), fall=0.1, rise=0.5)

    for fbins in freqbins:
        fbins = dsp.stretch(fbins, new_length=N)
        lowpass.update(fbins)
        difference = fbins - prevbins
        prevbins = fbins.copy()
        # Assign color channels.
        r = r_lowpass.update(fbins - lowpass.value)
        g = g_lowpass.update(np.abs(difference))
        b = b_lowpass.update(fbins.copy())
        # Mirror the color channels for symmetric output
        r = np.concatenate((r[::-1], r))
        g = np.concatenate((g[::-1], g))
        b = np.concatenate((b[::-1], b))
        yield np.array([r, g, b])


def energy(freqbins, npixels, nbins, scale=0.9):
    pixels = np.tile(1.0, (3, npixels // 2))
    filt = dsp.RealTimeExpFilter(np.tile(1.0, (3, npixels // 2)), fall=0.1, rise=0.99)
    gain = dsp.RealTimeExpFilter(np.tile(0.1, nbins), fall=0.5, rise=0.5)

    for fbins in freqbins:
        gain.update(fbins)
        fbins = fbins / gain.value
        fbins *= (npixels // 2) - 1

        N = len(fbins)
        # Color magnitudes.
        r = int(np.mean(fbins[:N//3]**scale))
        g = int(np.mean(fbins[N//3: 2*N//3]**scale))
        b = int(np.mean(fbins[2*N//3:]**scale))
        # Assign color channels.
        pixels[0, :r] = 1.0
        pixels[0, r:] = 0.0
        pixels[1, :g] = 1.0
        pixels[1, g:] = 0.0
        pixels[2, :b] = 1.0
        pixels[2, b:] = 0.0
        filt.update(pixels)
        pixels = np.round(filt.value)
        # Apply substantial blur to smooth the edges
        pixels[0, :] = gaussian_filter1d(pixels[0, :], sigma=4.0)
        pixels[1, :] = gaussian_filter1d(pixels[1, :], sigma=4.0)
        pixels[2, :] = gaussian_filter1d(pixels[2, :], sigma=4.0)
        # Output pixel data.
        yield np.concatenate((pixels[:, ::-1], pixels), axis=1)


parser = argparse.ArgumentParser(description='Energy visualization.')
parser.add_argument('effect', type=str, help='Effect name.')
parser.add_argument('--pixels', required=True, type=int, help='Number of LED strip pixels')
parser.add_argument('--rate', type=int, default=None, help='Update rate in Hz')
parser.add_argument('--bins', type=int, default=30, help='Number of FFT bins')
parser.add_argument('--fmin', type=int, default=200, help='Min frequency (Hz)')
parser.add_argument('--fmax', type=int, default=2000, help='Max frequency (Hz)')


def main():
    args = parser.parse_args()
    effect = getattr(sys.modules[__name__], args.effect)

    if args.fmin >= args.fmax:
        parser.error('fmin must be less than fmax')

    # Effect parameters.
    samplerate = struct.unpack('>i', sys.stdin.buffer.read(4))[0]
    chunksize = samplerate // args.rate
    nbytes = 4 * chunksize
    filterbank = mel.filterbank(samplerate, args.rate, args.bins, args.fmin, args.fmax)

    # Signal processing pipeline.
    chunks = audio.yield_chunks(nbytes, sys.stdin.buffer)
    freqbins = audio.melbins(chunks, filterbank.T, args.bins)
    pixels = effect(freqbins, args.pixels, args.bins)

    for pixelarray in pixels:
        tstart = time.clock()

        for n in range(pixelarray.shape[1]):
            pixel = '{}\t{:.3e}\t{:.3e}\t{:.3e}\n'.format(n, *pixelarray[:, n])
            sys.stdout.write(pixel)
        sys.stdout.flush()

        tstop = time.clock()
        tnorm = 1 / args.rate
        twait = tnorm - (tstop - tstart)
        early = twait >= 0

        if early:
            time.sleep(twait)
        else:
            msg = 'Late {:.2f} ms (1/f = {:.2f} ms)\n'.format(-twait * 1000, tnorm * 1000)
            sys.stderr.write(msg)

    sys.stdout.close()


if __name__ == '__main__':
    main()
