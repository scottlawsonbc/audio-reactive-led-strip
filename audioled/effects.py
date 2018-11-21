from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import time
import struct
import colorsys
import numpy as np
import audioled.dsp as dsp
import audioled.filtergraph as filtergraph
import math
from scipy.ndimage.filters import gaussian_filter1d
from scipy.signal import lfilter

SHORT_NORMALIZE = 1.0 / 32768.0

class Effect:
    """Base class for effects
    """

    def __init__(self):
        pass

    def update(self, scal_dt):
        """Update effect
        """
        raise NotImplementedError('update() was not implemented')

    def effect(self):
        """Process effect
        """
        raise NotImplementedError('effect() was not implemented')



class SpectrumEffect(Effect):

    def __init__(self, num_pixels, fs, audio_gen, bass_colorgen, melody_colorgen, fmax=6000, n_overlaps=8, chunk_rate=60, mirror_middle=True):
        self.norm_dist = np.linspace(0, 1, num_pixels)
        if mirror_middle:
            self.norm_dist = np.linspace(0, 1, num_pixels // 2)
        self.fft_bins = 64
        self.fft_dist = np.linspace(0, 1, self.fft_bins)
        self.chunk_rate = chunk_rate
        self.n_overlaps = n_overlaps
        self.fs = fs
        self.fmax = fmax
        self.mirror_middle = mirror_middle
        self.audio_gen = self._audio_gen(audio_gen)
        self.bass_colorgen = bass_colorgen
        self.melody_colorgen = melody_colorgen
        self.t = 0.0
        self.max_filter = np.ones(8)
        self.min_feature_win = np.hamming(4)
        self.cycle_time = 30.0
        self.chunk_rate = 60
        self.n_overlaps = 8
        self.fs_ds = 0.0
        self.bass_rms = None
        self.melody_rms = None

    def _audio_gen(self, audio_gen):
        self.bass_rms = np.zeros(self.chunk_rate * 6)
        self.melody_rms = np.zeros(self.chunk_rate * 6)
        audio, self.fs_ds = dsp.preprocess(audio_gen, self.fs, self.fmax, self.n_overlaps)
        for y in audio:
            yield y

    def effect(self):
        for y in self.audio_gen:
            bass = dsp.warped_psd(y, self.fft_bins, self.fs_ds, [32.7, 261.0], 'bark')
            melody = dsp.warped_psd(y, self.fft_bins, self.fs_ds, [261.0, self.fmax], 'bark')
            bass = self.process_line(bass, self.bass_rms)
            melody = self.process_line(melody, self.melody_rms)
            pixels = 1./255.0 * bass * self.bass_colorgen.get_color_array(self.t, 1) + 1./255.0 * melody * self.melody_colorgen.get_color_array(self.t, 1)
            yield pixels.clip(0, 255).astype(int)

    def update(self, scal_dt):
        self.t+=scal_dt

    def process_line(self, fft, fft_rms):
        fft = np.convolve(fft, self.max_filter, 'same')
        fft_rms[1:] = fft_rms[:-1]
        fft_rms[0] = np.mean(fft)
        fft = np.tanh(fft / np.max(fft_rms)) * 255
        fft = np.interp(self.norm_dist, self.fft_dist, fft)
        fft = np.convolve(fft, self.min_feature_win, 'same')
        if self.mirror_middle:
            fft = np.r_[fft, fft[::-1]]
        return fft




class ActivateAll(Effect):
    #testEffect for colors and dim

    def __init__(self, num_pixels, audio_gen, color_gen):
        self.num_pixels = num_pixels
        self.audio_gen = audio_gen
        self.color_gen = color_gen
        self.t = 0.0

    def update(self, scal_dt):
        self.t += scal_dt

    def effect(self):
        for y in self.audio_gen:
            bar = np.zeros(self.num_pixels) * np.array([[0], [0], [0]])
            index = self.num_pixels
            bar[0:3, 0:index] = self.color_gen.get_color_array(self.t, self.num_pixels)[0:3, 0:index]
            yield bar















class ShiftEffect(Effect):

    def __init__(self, num_pixels, pixel_gen, speed, dim_time=1.0):
        self.num_pixels = num_pixels
        self.pixel_gen = pixel_gen
        self.pixel_state = np.zeros(num_pixels) * np.array([[0.0],[0.0],[0.0]])
        self.speed = speed
        self.dim_time = dim_time
        self.t = 0.0
        self.last_t = 0.0

    def update(self, scal_dt):
        self.t+=scal_dt
    
    def effect(self):
        for y in self.pixel_gen:

            pixels = np.roll(self.pixel_state, -1, axis=1)
            pixels[0][0] = 0
            pixels[1][0] = 0
            pixels[2][0] = 0
            dt = self.t - self.last_t
            self.last_t = self.t
            if self.dim_time > 0:
                pixels *=(1-dt / self.dim_time)

            self.pixel_state = pixels + y
            yield self.pixel_state.clip(0.0,255.0)






# New Filtergraph Style effects

class VUMeterRMSEffect(filtergraph.Effect):
    """ VU Meter style effect
    Inputs:
    0: Audio
    1: Color
    """ 

    def __init__(self, num_pixels, db_range = 60.0):
        self.num_pixels = num_pixels
        self.db_range = db_range
        self._inputBuffer = None
        self._outputBuffer = None
        super(VUMeterRMSEffect, self).__init__()

    def numInputChannels(self):
        return 2
    def numOutputChannels(self):
        return 1

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

class VUMeterPeakEffect(filtergraph.Effect):
    """ VU Meter style effect
    Inputs:
    0: Audio
    1: Color
    """ 

    def __init__(self, num_pixels, db_range = 60.0):
        self.num_pixels = num_pixels
        self.db_range = db_range
        self._inputBuffer = None
        self._outputBuffer = None
        super(VUMeterPeakEffect, self).__init__()

    def numInputChannels(self):
        return 2
    def numOutputChannels(self):
        return 1

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

class MovingLightEffect(filtergraph.Effect):


    def __init__(self, num_pixels, fs, speed=10.0, dim_time=20.0, lowcut_hz=50.0, highcut_hz=300.0):
        self.num_pixels = num_pixels
        self.pixel_state = np.zeros(num_pixels) * np.array([[0.0],[0.0],[0.0]])
        self.speed = speed
        self.dim_time = dim_time
        self.filter_b, self.filter_a, self.filter_zi = dsp.design_filter(lowcut_hz, highcut_hz, fs, 3)
        self.last_t = 0.0
        self.last_move_t = 0.0
        super(MovingLightEffect, self).__init__()

    def numInputChannels(self):
        return 2
    
    def numOutputChannels(self):
        return 1
    
    def process(self):
        if self._inputBuffer != None and self._outputBuffer != None:
            buffer = self._inputBuffer[0]
            color = self._inputBuffer[1]
            if color is None:
                # default color: all white
                color = np.ones(self.num_pixels) * np.array([[255.0],[255.0],[255.0]])
            if buffer is not None:
                audio = self._inputBuffer[0]
                # apply bandpass to audio
                y, self.filter_zi = lfilter(b=self.filter_b, a=self.filter_a, x=np.array(audio), zi=self.filter_zi)
                # move in speed
                dt_move = self.t - self.last_move_t
                if dt_move * self.speed > 1:
                    shift_pixels = int(dt_move * self.speed)
                    self.pixel_state[:, shift_pixels:] = self.pixel_state[:, :-shift_pixels]
                    self.pixel_state[:, 0:shift_pixels] = self.pixel_state[:, shift_pixels:shift_pixels+1]
                    # convolve to smooth edges
                    self.pixel_state[:, 0:2*shift_pixels] = gaussian_filter1d(self.pixel_state[:,0:2*shift_pixels],0.5)
                    self.last_move_t = self.t
                # dim with time
                dt = self.t - self.last_t
                self.last_t = self.t
                self.pixel_state*= (1.0 - dt / self.dim_time)
                self.pixel_state = gaussian_filter1d(self.pixel_state, sigma=0.5)
                self.pixel_state = gaussian_filter1d(self.pixel_state, sigma=0.5)
                # new color at origin
                peak = dsp.rms(y) * 2.0
                peak = peak**2
                r,g,b = color[0,0], color[1,0], color[2,0]
                self.pixel_state[0][0] = r * peak + peak * 255.0
                self.pixel_state[1][0] = g * peak+ peak * 255.0
                self.pixel_state[2][0] = b * peak+ peak * 255.0
                self._outputBuffer[0] = self.pixel_state.clip(0.0,255.0)

class AfterGlowEffect(filtergraph.Effect):

    def __init__(self, num_pixels, glow_time=1.0):
        self.num_pixels = num_pixels
        self.pixel_state = np.zeros(num_pixels) * np.array([[0.0],[0.0],[0.0]])
        self.glow_time = glow_time
        self.last_t = 0.0
        super(AfterGlowEffect, self).__init__()

    def numInputChannels(self):
        return 1
    
    def numOutputChannels(self):
        return 1

    
    def process(self):
        if self._inputBuffer is not None and self._outputBuffer is not None:
            y = self._inputBuffer[0]
            if y is not None:
                dt = self.t - self.last_t
                self.last_t = self.t
                
                if dt > 0:
                    self.pixel_state*= (1.0 - dt / self.glow_time)
                    self.pixel_state = self.pixel_state.clip(0.0, 255.0)
                self.pixel_state = np.maximum(self.pixel_state, y)
                self.pixel_state = self.pixel_state.clip(0.0, 255.0)
                self._outputBuffer[0] = self.pixel_state

class MirrorEffect(filtergraph.Effect):

    def __init__(self, num_pixels, mirror_lower = True):
        self.num_pixels = num_pixels
        self.mirror_lower = mirror_lower
        super(MirrorEffect, self).__init__()

    def numInputChannels(self):
        return 1
    
    def numOutputChannels(self):
        return 1

    def process(self):
        if self._inputBuffer is not None and self._outputBuffer is not None:
            n = self.num_pixels
            h = int(n/2)
            buffer = self._inputBuffer[0]
            if buffer is not None:
                y = buffer.copy()
                # 0 .. h .. n
                #   h    n-h
                if self.mirror_lower:
                    # take lower values
                    temp = y[:,0:h]
                    # reverse
                    temp = temp[:,::-1]
                    # assign reverse to upper part
                    y[:,h:n] = temp[:,0:h]
                    self._outputBuffer[0] = y
                else:
                    # take higher values
                    temp = y[:,h:n] # lenght: n-h
                    # reverse
                    temp = temp[:,::-1]
                    # assign reverse to lower part
                    y[:,0:n-h] = temp[:,0:n-h]
                    
                    self._outputBuffer[0] = y