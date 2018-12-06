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
import audioled.filtergraph as filtergraph
from audioled.effect import Effect


class Swimmingpool(Effect):

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
        super(Swimmingpool, self).__initstate__()

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "num_pixels": [300, 1, 1000, 1],
                "num_waves": [30, 1, 100, 1],
                "scale": [0.2, 0.01, 1.0, 0.01],
                "wavespread_low": [30, 1, 100, 1],
                "wavespread_high": [70, 50, 150, 1],
                "max_speed": [30, 1, 200, 1],

            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        del definition['parameters']['num_pixels']
        definition['parameters']['num_waves'][0] = self.num_waves
        definition['parameters']['scale'][0] = self.scale
        definition['parameters']['wavespread_low'][0] = self.wavespread_low
        definition['parameters']['wavespread_high'][0] = self.wavespread_high
        definition['parameters']['max_speed'][0] = self.max_speed
        return definition

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
        return 2

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



class DefenceMode(Effect):

    def __init__(self, num_pixels, scale=0.2):
        self.num_pixels = num_pixels
        self.scale = scale
        self.__initstate__()

    def __initstate__(self):
        # state
        self._pixel_state = np.zeros(self.num_pixels) * np.array([[0.0], [0.0], [0.0]])
        self._last_t = 0.0
        super(DefenceMode, self).__initstate__()

    def numInputChannels(self):
        return 1

    def numOutputChannels(self):
        return 1

    def process(self):
        if self._outputBuffer is not None:
            #color = self._inputBuffer[0]
            A = random.choice([True,False,False])
            if A == True:
                self._output = np.ones(self.num_pixels) * np.array([[random.randint(0.0,255.0)], [random.randint(0.0,255.0)], [random.randint(0.0,255.0)]])
            else:
                self._output = np.zeros(self.num_pixels) * np.array([[0.0], [0.0], [0.0]])

            self._outputBuffer[0] = self._output.clip(0.0,255.0)
