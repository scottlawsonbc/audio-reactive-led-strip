from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import time
import struct
import colorsys
import asyncio
import numpy as np
import audioled.dsp as dsp
import audioled.filtergraph as filtergraph
import math
from scipy.ndimage.filters import gaussian_filter1d
from scipy.signal import lfilter

SHORT_NORMALIZE = 1.0 / 32768.0

class Effect(object):
    """
    Base class for effects

    Effects have a number of input channels and a number of output channels.
    Before each processing the effect is updated.

    Input values can be accessed by self._inputBuffer[channelNumber], output values
    are to be written into self_outputBuffer[channelNumber].
    """
    def __init__(self):
        self.__initstate__()

    def __initstate__(self):
        self._t = 0.0
        self._inputBuffer = None
        self._outputBuffer = None

    def numOutputChannels(self):
        """
        Returns the number of output channels for this effect
        """
        raise NotImplementedError('numOutputChannels() was not implemented')

    def numInputChannels(self):
        """
        Returns the number of input channels for this effect.
        """
        raise NotImplementedError('numInputChannels() was not implemented')

    def setOutputBuffer(self,buffer):
        """
        Set output buffer where processed data is to be written
        """
        self._outputBuffer = buffer

    def setInputBuffer(self, buffer):
        """
        Set input buffer for incoming data
        """
        self._inputBuffer = buffer

    def process(self):
        """
        The main processing function:
        - Read input data from self._inputBuffer
        - Process data
        - Write output data to self._outputBuffer
        """
        raise NotImplementedError('process() was not implemented')
    
    async def update(self, dt):
        """
        Update timing, can be used to precalculate stuff that doesn't depend on input values
        """
        self._t += dt

    def __cleanState__(self, stateDict):
        """
        Cleans given state dictionary from state objects beginning with __
        """
        for k in list(stateDict.keys()):
            if k.startswith('_'):
                stateDict.pop(k)
        return stateDict
        
    def __getstate__(self):
        """
        Default implementation of __getstate__ that deletes buffer, call __cleanState__ when overloading
        """
        state = self.__dict__.copy()
        self.__cleanState__(state)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__initstate__()


class SpectrumEffect(Effect):
    """
    SpectrumEffect performs a FFT and visualizes bass and melody frequencies with different colors.

    Inputs:
    - 0: Audio
    - 1: Color for melody (default: white)
    - 2: Color for bass (default: white)

    Outputs:
    - 0: Pixel array

    """

    def __init__(self, num_pixels, fs, fmax=6000, n_overlaps=8, chunk_rate=60, mirror_middle=True):
        self.num_pixels = num_pixels
        self.fs = fs
        self.fmax = fmax
        self.n_overlaps = n_overlaps
        self.chunk_rate = chunk_rate
        self.mirror_middle = mirror_middle
        self.__initstate__()

    def __initstate__(self):
        # state
        self._norm_dist = np.linspace(0, 1, self.num_pixels)
        if self.mirror_middle:
            self._norm_dist = np.linspace(0, 1, self.num_pixels // 2)
        self._fft_bins = 64
        self._fft_dist = np.linspace(0, 1, self._fft_bins)
        self._max_filter = np.ones(8)
        self._min_feature_win = np.hamming(4)
        self._fs_ds = 0.0
        self._bass_rms = None
        self._melody_rms = None
        self._lastAudioChunk = None
        self._gen = None
        super(SpectrumEffect, self).__initstate__()

    def numInputChannels(self):
        return 3

    def numOutputChannels(self):
        return 1

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
                bass = dsp.warped_psd(y, self._fft_bins, self._fs_ds, [32.7, 261.0], 'bark')
                melody = dsp.warped_psd(y, self._fft_bins, self._fs_ds, [261.0, self.fmax], 'bark')
                bass = self.process_line(bass, self._bass_rms)
                melody = self.process_line(melody, self._melody_rms)
                pixels = 1./255.0 * np.multiply(bass, col_bass) + 1./255.0 * np.multiply(melody, col_melody)
                self._outputBuffer[0] = pixels.clip(0,255).astype(int)

    def process_line(self, fft, fft_rms):
        fft = np.convolve(fft, self._max_filter, 'same')
        fft_rms[1:] = fft_rms[:-1]
        fft_rms[0] = np.mean(fft)
        fft = np.tanh(fft / np.max(fft_rms)) * 255
        fft = np.interp(self._norm_dist, self._fft_dist, fft)
        fft = np.convolve(fft, self._min_feature_win, 'same')
        if self.mirror_middle:
            fft = np.r_[fft, fft[::-1]]
        return fft


class ShiftEffect(Effect):
    
    def __init__(self, num_pixels, speed=2.0, dim_time=.1):
        self.num_pixels = num_pixels
        self.speed = speed
        self.dim_time = dim_time
        self.__initstate__()

    def __initstate__(self):
        # state
        self._pixel_state = np.zeros(self.num_pixels) * np.array([[0.0],[0.0],[0.0]])
        self._last_t = 0.0
        super(ShiftEffect, self).__initstate__()

    def numInputChannels(self):
        return 1

    def numOutputChannels(self):
        return 1
    
    def process(self):
        if self._inputBuffer is not None and self._outputBuffer is not None:
            pixels = self._inputBuffer[0]
            if pixels is not None:
                y = pixels
                pixels = np.roll(self._pixel_state, -1, axis=1)
                pixels[0][0] = 0
                pixels[1][0] = 0
                pixels[2][0] = 0
                dt = self._t - self._last_t
                self._last_t = self._t
                if self.dim_time > 0:
                    pixels *=(1-dt / self.dim_time)

                self._pixel_state = pixels + y
                self._outputBuffer[0] = self._pixel_state.clip(0.0,255.0)


class VUMeterRMSEffect(Effect):
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

class VUMeterPeakEffect(Effect):
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



class MovingLightEffect(Effect):
    """
    This effect generates a peak at the beginning of the strip that moves and dissipates

    Inputs:
    - 0: Audio
    - 1: Color
    """

    def __init__(self, num_pixels, fs, speed=10.0, dim_time=20.0, lowcut_hz=50.0, highcut_hz=300.0):
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
        super(MovingLightEffect, self).__initstate__()

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
                y, self._filter_zi = lfilter(b=self._filter_b, a=self._filter_a, x=np.array(audio), zi=self._filter_zi)
                # move in speed
                dt_move = self._t - self._last_move_t
                if dt_move * self.speed > 1:
                    shift_pixels = int(dt_move * self.speed)
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
                peak = dsp.rms(y) * 2.0
                peak = peak**2
                r,g,b = color[0,0], color[1,0], color[2,0]
                self._pixel_state[0][0] = r * peak + peak * 255.0
                self._pixel_state[1][0] = g * peak+ peak * 255.0
                self._pixel_state[2][0] = b * peak+ peak * 255.0
                self._outputBuffer[0] = self._pixel_state.clip(0.0,255.0)



class AfterGlowEffect(Effect):
    """
    Effect that 
    """

    def __init__(self, num_pixels, glow_time=1.0):
        self.num_pixels = num_pixels
        self.glow_time = glow_time
        self.__initstate__()

    def __initstate__(self):
        # state
        self._pixel_state = np.zeros(self.num_pixels) * np.array([[0.0],[0.0],[0.0]])
        self._last_t = 0.0
        super(AfterGlowEffect, self).__initstate__()

    def numInputChannels(self):
        return 1
    
    def numOutputChannels(self):
        return 1

    
    def process(self):
        if self._inputBuffer is not None and self._outputBuffer is not None:
            y = self._inputBuffer[0]
            if y is not None:
                dt = self._t - self._last_t
                self._last_t = self._t
                
                if dt > 0:
                    self._pixel_state*= (1.0 - dt / self.glow_time)
                    self._pixel_state = self._pixel_state.clip(0.0, 255.0)
                self._pixel_state = np.maximum(self._pixel_state, y)
                self._pixel_state = self._pixel_state.clip(0.0, 255.0)
                self._outputBuffer[0] = self._pixel_state

class MirrorEffect(Effect):

    def __init__(self, num_pixels, mirror_lower = True, recursion = 0):
        self.num_pixels = num_pixels
        self.mirror_lower = mirror_lower
        self.recursion = recursion
        self.__initstate__()

    def __initstate__(self):
        # state
        self._mirrorLower = self._genMirrorLowerMap(self.num_pixels,self.recursion)
        self._mirrorUpper = self._genMirrorUpperMap(self.num_pixels,self.recursion)
        super(MirrorEffect, self).__initstate__()

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
                y = buffer
                # 0 .. h .. n
                #   h    n-h
                if self.mirror_lower:
                    self._outputBuffer[0] = buffer[self._mirrorLower[:,:,0],self._mirrorLower[:,:,1]]
                    # # take lower values
                    # temp = y[:,0:h]
                    # # reverse
                    # temp = temp[:,::-1]
                    # # assign reverse to upper part
                    # y[:,h:n] = temp[:,0:h]
                    # self._outputBuffer[0] = y
                else:
                    self._outputBuffer[0] = buffer[self._mirrorUpper[:,:,0],self._mirrorUpper[:,:,1]]
                    # # take higher values
                    # temp = y[:,h:n] # lenght: n-h
                    # # reverse
                    # temp = temp[:,::-1]
                    # # assign reverse to lower part
                    # y[:,0:n-h] = temp[:,0:n-h]
                    
                    # self._outputBuffer[0] = y

    def _genMirrorLowerMap(self, n, recursion):
        h = int(n/2)
        mapMask = np.array([[[0,i] for i in range(0,n)],
                                [[1,i] for i in range(0,n)],
                                [[2,i] for i in range(0,n)]],dtype=np.int64)
        mapMask = self._genMirrorLower(mapMask,recursion)
        return mapMask

    def _genMirrorLower(self, mask, recurse=0):
        mapMask = mask.copy()
        n = mapMask.shape[1]
        if n%2 == 1:
            n=n-1
        h = int(n/2)
        temp = mapMask[:,0:h,:]
        temp = temp[:,::-1,:]
        mapMask[:,h:n,:] = temp[:,0:h,:]
        if recurse > 0:
            mapMask[:,0:h,:] = self._genMirrorLower(mapMask[:,0:h,:], recurse-1)
            mapMask[:,h:n,:] = self._genMirrorUpper(mapMask[:,h:n,:], recurse-1)
        return mapMask

    def _genMirrorUpperMap(self, n, recursion):
        h = int(n/2)
        mapMask = np.array([[[0,i] for i in range(0,n)],
                                [[1,i] for i in range(0,n)],
                                [[2,i] for i in range(0,n)]],dtype=np.int64)
        mapMask = self._genMirrorUpper(mapMask,recursion)
        return mapMask

    def _genMirrorUpper(self,mask, recurse=0):
        mapMask = mask.copy()
        n=mapMask.shape[1]
        if n%2 == 1:
            n=n-1
        h = int(n/2)
        # take upper part
        temp = mapMask[:,h:n,:]
        # revert
        temp = temp[:,::-1,:]
        # assign to lower part
        mapMask[:,0:n-h,:] = temp[:,0:n-h,:]
        if recurse > 0:
            mapMask[:,0:h,:] = self._genMirrorUpper(mapMask[:,0:h,:], recurse-1)
            mapMask[:,h:n,:] = self._genMirrorLower(mapMask[:,h:n,:], recurse-1)
        return mapMask
    