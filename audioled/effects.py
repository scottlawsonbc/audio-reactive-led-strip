from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import time
import colorsys
import numpy as np
import audioled.dsp as dsp


def spectrum(pixels, fs, fmax=6000, n_overlaps=8, chunk_rate=60):
    fft_bins = 128
    max_filter = np.ones(16)
    min_feature_win = np.hamming(4)
    norm_dist = np.linspace(0, 1, pixels // 2)
    fft_dist = np.linspace(0, 1, fft_bins)
    cycle_time = 30.0

    def color(t, L=0.5, S=1.0):
        h = (t % cycle_time) / cycle_time
        r, g, b = colorsys.hls_to_rgb(h, L, S)
        return np.array([[r], [g], [b]])

    def process_line(fft, fft_rms):
        fft = np.convolve(fft, max_filter, 'same')
        fft_rms[1:] = fft_rms[:-1]
        fft_rms[0] = np.mean(fft)
        fft = np.tanh(fft / np.max(fft_rms)) * 255
        fft = np.interp(norm_dist, fft_dist, fft)
        fft = np.convolve(fft, min_feature_win, 'same')
        fft = np.r_[fft, fft[::-1]]
        return fft

    def effect(audio):
        bass_rms = np.zeros(chunk_rate * 6)
        melody_rms = np.zeros(chunk_rate * 6)
        audio, fs_ds = dsp.preprocess(audio, fs, fmax, n_overlaps)
        for y in audio:
            bass = dsp.warped_psd(y, fft_bins, fs_ds, [32.7, 261.0], 'bark')
            melody = dsp.warped_psd(y, fft_bins, fs_ds, [261.0, fmax], 'bark')
            bass = process_line(bass, bass_rms)
            melody = process_line(melody, melody_rms)
            t = time.time()
            pixels = bass * color(t) + melody * color(t + cycle_time / 2)
            yield pixels.clip(0, 255).astype(int)
    return effect
