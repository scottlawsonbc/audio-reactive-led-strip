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
import random
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
        try:
            self._inputBuffer
        except AttributeError:
            self._inputBuffer = None
        try:
            self._outputBuffer
        except AttributeError:
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
    
    def updateParameter(self, stateDict):
        self.__setstate__(stateDict)

    def getParameter(self):
        return {}

    @staticmethod
    def getParameterDefinition():
        return {}


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

    def __init__(self, num_pixels, fs, fmax=6000, n_overlaps=4, chunk_rate=60, fft_bins=64, col_blend = 'lightenOnly'):
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
                bass = dsp.warped_psd(y, self.fft_bins, self._fs_ds, [32.7, 261.0], 'bark')
                melody = dsp.warped_psd(y, self.fft_bins, self._fs_ds, [261.0, self.fmax], 'bark')
                bass = self.process_line(bass, self._bass_rms)
                melody = self.process_line(melody, self._melody_rms)
                if self.col_blend == 'lightenOnly':
                    pixels = np.maximum(1./255.0 * np.multiply(col_bass, bass), 1./255. * np.multiply(col_melody, melody))
                else:
                    pixels = 1./255.0 * np.multiply(col_bass, bass) + 1./255. * np.multiply(col_melody, melody)
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



class MovingLightEffect(Effect):
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
        super(MovingLightEffect, self).__initstate__()

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



class Append(Effect):
    def __init__(self, num_channels, flip0=False, flip1=False, flip2=False, flip3=False, flip4=False, flip5=False, flip6=False, flip7=False):
        self.num_channels = num_channels
        self.flip0 = flip0
        self.flip1 = flip1
        self.flip2 = flip2
        self.flip3 = flip3
        self.flip4 = flip4
        self.flip5 = flip5
        self.flip6 = flip6
        self.flip7 = flip7
        self.__initstate__()
    
    def __initstate__(self):
        super().__initstate__()
        self._flipMask = [self.flip0,self.flip1,self.flip2,self.flip3,self.flip4,self.flip5,self.flip6,self.flip7]

    def numInputChannels(self):
        return self.num_channels
    
    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "num_channels": [2, 1, 8, 1],
                "flip0": False,
                "flip1": False,
                "flip2": False,
                "flip3": False,
                "flip4": False,
                "flip5": False,
                "flip6": False,
                "flip7": False,
            }
        }
        return definition
    
    def getParameter(self):
        definition = self.getParameterDefinition()
        del definition['parameters']['num_channels'] # not editable at runtime
        definition['parameters']['flip0'] = self.flip0
        definition['parameters']['flip1'] = self.flip1
        definition['parameters']['flip2'] = self.flip2
        definition['parameters']['flip3'] = self.flip3
        definition['parameters']['flip4'] = self.flip4
        definition['parameters']['flip5'] = self.flip5
        definition['parameters']['flip6'] = self.flip6
        definition['parameters']['flip7'] = self.flip7
        return definition

    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            self._outputBuffer[0] = None
            return
        if self._inputBuffer[0] is None:
            self._outputBuffer[0] = None
            return
        state = np.zeros((3,0))
        for i in range(0,self.num_channels):
            if self._inputBuffer[i] is not None:
                if self._flipMask is not None and self._flipMask[i] > 0:
                    state = np.concatenate((state, self._inputBuffer[i][:,::-1]),axis=1)
                else:
                    state = np.concatenate((state, self._inputBuffer[i]),axis=1)    
        self._outputBuffer[0] = state

class Combine(Effect):
    def __init__(self, mode='lightenOnly'):
        self.mode = mode
        self.__initstate__()
    
    def numInputChannels(self):
        return 2
    
    def numOutputChannels(self):
        return 1
    
    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            return
        if self.mode == 'lightenOnly':
            self._outputBuffer[0] = np.maximum(self._inputBuffer[0], self._inputBuffer[1])
        

class AfterGlowEffect(Effect):
    """
    Effect that 
    """

    def __init__(self, glow_time=1.0):
        self.glow_time = glow_time
        self.__initstate__()

    def __initstate__(self):
        # state
        self._pixel_state = None
        self._last_t = 0.0
        super(AfterGlowEffect, self).__initstate__()

    def numInputChannels(self):
        return 1
    
    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "glow_time": [1.0, 0.0, 10.0, 0.01],
            }
        }
        return definition
    
    def getParameter(self):
        definition = self.getParameterDefinition()       
        definition['parameters']['glow_time'][0] = self.glow_time
        return definition

    async def update(self, dt):
        await super().update(dt)
        dt = self._t - self._last_t
        self._last_t = self._t
        
        if dt > 0:
            # Dim state
            if self.glow_time > 0 and self._pixel_state is not None:
                self._pixel_state = self._pixel_state * (1.0 - dt / self.glow_time)
            else:
                self._pixel_state = None
    
    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            self._outputBuffer[0] = None
            return
        y = self._inputBuffer[0]
        if y is None:
            self._outputBuffer[0] = None
            return
        
        if self._pixel_state is not None and np.size(self._pixel_state) == np.size(y):
            # keep previous state if new color is too dark
            diff = (y - self._pixel_state).max(axis=0)
            mask = diff < 10
            
            y [:,mask]= self._pixel_state[:,mask]

        self._pixel_state = y
    
        self._outputBuffer[0] = y

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
                else:
                    self._outputBuffer[0] = buffer[self._mirrorUpper[:,:,0],self._mirrorUpper[:,:,1]]

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



class SwimmingpoolEffect(Effect):

    def __init__(self, num_pixels, num_waves=30, scale=0.2, wavespread_low=30, wavespread_high=70, max_speed=30):
        self.num_pixels = num_pixels
        self.num_waves = num_waves
        self.scale = scale
        self.wavespread_low = wavespread_low
        self.wavespread_high = wavespread_high
        self.max_speed = max_speed
        self.__initstate__()

    def __initstate__(self):
        # state
        self._pixel_state = np.zeros(self.num_pixels) * np.array([[0.0], [0.0], [0.0]])
        self._last_t = 0.0
        self._output = np.copy(self._pixel_state)
        self._Wave, self._WaveSpecSpeed = self._CreateWaves(self.num_waves, self.scale, self.wavespread_low, self.wavespread_high, self.max_speed)
        super(SwimmingpoolEffect, self).__initstate__()

    def _SinArray(self, _spread, _scale, _wavehight):
        _CArray = []
        _offset = random.randint(0,300)
        for i in range(-_spread, _spread+1):
            _CArray.append(math.sin((math.pi/_spread) * i) * _scale * _wavehight * 255)
            _output = np.copy(self._pixel_state)
            _output[0][:len(_CArray)] += _CArray
            _output[1][:len(_CArray)] += _CArray
            _output[2][:len(_CArray)] += _CArray
        return _output.clip(0.0,255.0)

    def _CreateWaves(self, num_waves, scale, wavespread_low=10, wavespread_high=50, max_speed=30):
        _WaveArray = []
        _WaveArraySpec = []
        _wavespread = np.random.randint(wavespread_low,wavespread_high,num_waves)
        _WaveArraySpecSpeed = np.random.randint(-max_speed,max_speed,num_waves)
        _WaveArraySpecHeight = np.random.rand(num_waves)
        for i in range(0, num_waves):
            _WaveArray.append(self._SinArray(_wavespread[i], scale, _WaveArraySpecHeight[i]))
        return _WaveArray, _WaveArraySpecSpeed;

    def numInputChannels(self):
        return 1

    def numOutputChannels(self):
        return 1

    def process(self):
        if self._outputBuffer is not None:
            color = self._inputBuffer[0]
            self._output = 0.5 * np.ones(self.num_pixels) * color

            for i in range(0,self.num_waves):
                step = np.roll(self._Wave[i], int(self._t * self._WaveSpecSpeed[i]), axis=1)
                self._output += step

            self._outputBuffer[0] = self._output.clip(0.0,255.0)