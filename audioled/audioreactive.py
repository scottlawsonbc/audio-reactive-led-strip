from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import asyncio
import colorsys
import math
import random
import struct
import time

import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
from scipy.signal import lfilter

import audioled.dsp as dsp
import audioled.colors as colors
import audioled.filtergraph as filtergraph
from audioled.effects import Effect


class Spectrum(Effect):
    """
    SpectrumEffect performs a FFT and visualizes bass and melody frequencies with different colors.

    Inputs:
    - 0: Audio
    - 1: Color for melody (default: white)
    - 2: Color for bass (default: white)

    Outputs:
    - 0: Pixel array

    """

    def __init__(self, num_pixels, fs, fmax=6000, n_overlaps=4, chunk_rate=60, fft_bins=64, col_blend = colors.blend_mode_default):
        self.num_pixels = num_pixels
        self.fs = fs
        self.fmax = fmax
        self.n_overlaps = n_overlaps
        self.chunk_rate = chunk_rate
        self.fft_bins = fft_bins
        self.col_blend = col_blend
        self.__initstate__()

    def __initstate__(self):
        # state
        self._norm_dist = np.linspace(0, 1, self.num_pixels)
        self.fft_bins = 64
        self._fft_dist = np.linspace(0, 1, self.fft_bins)
        self._max_filter = np.ones(8)
        self._min_feature_win = np.hamming(8)
        self._fs_ds = 0.0
        self._bass_rms = None
        self._melody_rms = None
        self._lastAudioChunk = None
        self._gen = None
        super(Spectrum, self).__initstate__()

    def numInputChannels(self):
        return 3

    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "num_pixels": [300, 1, 1000, 1],
                "fs": [48000, 44100, 96000, 100],
                "n_overlaps": [4, 0, 20, 1],
                "chunk_rate": [60, 30, 100, 1],
                "fft_bins": [64, 32, 128, 1],
                "col_blend": colors.blend_modes
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        #definition['parameters']['num_pixels'][0] = self.num_pixels
        del definition['parameters']['num_pixels'] # disable edit
        del definition['parameters']['fs'] # disable edit
        definition['parameters']['n_overlaps'][0] = self.n_overlaps
        definition['parameters']['chunk_rate'][0] = self.chunk_rate
        definition['parameters']['fft_bins'][0] = self.chunk_rate
        definition['parameters']['col_blend'] = [self.col_blend] + [x for x in colors.blend_modes if x!=self.col_blend]
        return definition

    def _audio_gen(self, audio_gen):
        self._bass_rms = np.zeros(self.chunk_rate * 6)
        self._melody_rms = np.zeros(self.chunk_rate * 6)
        audio, self._fs_ds = dsp.preprocess(audio_gen, self.fs, self.fmax, self.n_overlaps)
        return audio

    def buffer_coroutine(self):
        while True:
            yield self._lastAudioChunk

    def process(self):

        if self._inputBuffer is not None and self._outputBuffer is not None:
            audio = self._inputBuffer[0]
            col_melody = self._inputBuffer[1]
            col_bass = self._inputBuffer[2]
            if col_melody is None:
                # default color: all white
                col_melody = np.ones(self.num_pixels) * np.array([[255.0],[255.0],[255.0]])
            if col_bass is None:
                # default color: all white
                col_bass = np.ones(self.num_pixels) * np.array([[255.0],[255.0],[255.0]])
            if audio is not None:
                if self._gen is None:
                    g = self.buffer_coroutine()
                    next(g)
                    self._lastAudioChunk = audio
                    self._gen = self._audio_gen(g)
                self._lastAudioChunk = audio
                y = next(self._gen)
                bass = dsp.warped_psd(y, self.fft_bins, self._fs_ds, [32.7, 261.0], 'bark')
                melody = dsp.warped_psd(y, self.fft_bins, self._fs_ds, [261.0, self.fmax], 'bark')
                bass = self.process_line(bass, self._bass_rms)
                melody = self.process_line(melody, self._melody_rms)
                pixels = colors.blend(1./255.0 * np.multiply(col_bass, bass ), 1./255. * np.multiply(col_melody, melody), self.col_blend)
                self._outputBuffer[0] = pixels.clip(0,255).astype(int)

    def process_line(self, fft, fft_rms):

        #fft = np.convolve(fft, self._max_filter, 'same')

        # Some kind of normalization?
        #fft_rms[1:] = fft_rms[:-1]
        #fft_rms[0] = np.mean(fft)
        #fft = np.tanh(fft / np.max(fft_rms)) * 255

        # Upsample to number of pixels
        fft = np.interp(self._norm_dist, self._fft_dist, fft)

        #
        fft = np.convolve(fft, self._min_feature_win, 'same')

        return fft*255


class VUMeterRMS(Effect):
    """ VU Meter style effect
    Inputs:
    - 0: Audio
    - 1: Color
    """

    def __init__(self, num_pixels, db_range = 60.0):
        self.num_pixels = num_pixels
        self.db_range = db_range
        self.__initstate__()


    def numInputChannels(self):
        return 2
    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "num_pixels": [300, 1, 1000, 1],
                "db_range": [60.0, 20.0, 100.0, 1.0],
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        #definition['parameters']['num_pixels'][0] = self.num_pixels
        del definition['parameters']['num_pixels'] # disable edit
        definition['parameters']['db_range'][0] = self.db_range
        return definition

    def process(self):
        if self._inputBuffer != None and self._outputBuffer != None:
            buffer = self._inputBuffer[0]
            color = self._inputBuffer[1]
            if color is None:
                # default color: all white
                color = np.ones(self.num_pixels) * np.array([[255.0],[255.0],[255.0]])
            if buffer is not None:
                y = self._inputBuffer[0]
                N = len(y) # blocksize
                rms = dsp.rms(y)
                db = 20 * math.log10(max(rms, 1e-16))

                bar = np.zeros(self.num_pixels) * np.array([[0],[0],[0]])
                index = int(self.num_pixels * rms)
                index = np.clip(index, 0, self.num_pixels-1)
                bar[0:3,0:index] = color[0:3,0:index]
                self._outputBuffer[0] = bar



class VUMeterPeak(Effect):
    """ VU Meter style effect
    Inputs:
    - 0: Audio
    - 1: Color
    """

    def __init__(self, num_pixels, db_range = 60.0):
        self.num_pixels = num_pixels
        self.db_range = db_range
        self.__initstate__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "num_pixels": [300, 1, 1000, 1],
                "db_range": [60.0, 20.0, 100.0, 1.0],
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        #definition['parameters']['num_pixels'][0] = self.num_pixels
        del definition['parameters']['num_pixels'] # disable edit
        definition['parameters']['db_range'][0] = self.db_range
        return definition

    def process(self):
        if self._inputBuffer != None and self._outputBuffer != None:
            buffer = self._inputBuffer[0]
            color = self._inputBuffer[1]
            if color is None:
                # default color: all white
                color = np.ones(self.num_pixels) * np.array([[255.0],[255.0],[255.0]])
            if buffer is not None:
                y = self._inputBuffer[0]

                N = len(y) # blocksize
                peak = np.max(y)
                db = (20*(math.log10(max(peak, 1e-16))))
                scal_value = (self.db_range+db)/self.db_range
                bar = np.zeros(self.num_pixels) * np.array([[0],[0],[0]])
                index = int(self.num_pixels * scal_value)
                index = np.clip(index, 0, self.num_pixels-1)
                bar[0:3,0:index] = color[0:3,0:index]
                self._outputBuffer[0] = bar



class MovingLight(Effect):
    """
    This effect generates a peak at the beginning of the strip that moves and dissipates

    Inputs:
    - 0: Audio
    - 1: Color
    """

    def __init__(self, num_pixels, fs, speed=100.0, dim_time=2.0, lowcut_hz=50.0, highcut_hz=300.0):
        self.num_pixels = num_pixels
        self.speed = speed
        self.dim_time = dim_time
        self.fs = fs
        self.lowcut_hz = lowcut_hz
        self.highcut_hz = highcut_hz
        self.__initstate__()

    def __initstate__(self):
        # state
        self._pixel_state = np.zeros(self.num_pixels) * np.array([[0.0],[0.0],[0.0]])
        self._filter_b, self._filter_a, self._filter_zi = dsp.design_filter(self.lowcut_hz, self.highcut_hz, self.fs, 3)
        self._last_t = 0.0
        self._last_move_t = 0.0
        super(MovingLight, self).__initstate__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "speed": [10.0, 1.0, 200.0, 1.0],
                "dim_time": [2.0, 0.0, 100.0, 1.0],
                "lowcut_hz": [50.0, 0.0, 8000.0, 1.0],
                "highcut_hz": [100.0, 0.0, 8000.0, 1.0],
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        definition['parameters']['speed'][0] = self.speed
        definition['parameters']['dim_time'][0] = self.dim_time
        definition['parameters']['lowcut_hz'][0] = self.lowcut_hz
        definition['parameters']['highcut_hz'][0] = self.highcut_hz
        return definition

    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            return
        buffer = self._inputBuffer[0]
        color = self._inputBuffer[1]
        if color is None:
            # default color: all white
            color = np.ones(self.num_pixels) * np.array([[255.0],[255.0],[255.0]])
        if buffer is not None:
            audio = self._inputBuffer[0]
            # apply bandpass to audio
            y, self._filter_zi = lfilter(b=self._filter_b, a=self._filter_a, x=np.array(audio), zi=self._filter_zi)
            # move in speed
            dt_move = self._t - self._last_move_t
            if dt_move * self.speed > 1:
                shift_pixels = int(dt_move * self.speed)
                shift_pixels = np.clip(shift_pixels, 1, self.num_pixels-1)
                self._pixel_state[:, shift_pixels:] = self._pixel_state[:, :-shift_pixels]
                self._pixel_state[:, 0:shift_pixels] = self._pixel_state[:, shift_pixels:shift_pixels+1]
                # convolve to smooth edges
                self._pixel_state[:, 0:2*shift_pixels] = gaussian_filter1d(self._pixel_state[:,0:2*shift_pixels],0.5)
                self._last_move_t = self._t
            # dim with time
            dt = self._t - self._last_t
            self._last_t = self._t
            self._pixel_state*= (1.0 - dt / self.dim_time)
            self._pixel_state = gaussian_filter1d(self._pixel_state, sigma=0.5)
            self._pixel_state = gaussian_filter1d(self._pixel_state, sigma=0.5)
            # new color at origin
            peak = np.max(y) * 2.0
            peak = peak**2
            r,g,b = color[0,0], color[1,0], color[2,0]
            self._pixel_state[0][0] = r * peak + peak * 255.0
            self._pixel_state[1][0] = g * peak+ peak * 255.0
            self._pixel_state[2][0] = b * peak+ peak * 255.0
            self._outputBuffer[0] = self._pixel_state.clip(0.0,255.0)
