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
from audioled.effect import Effect

SHORT_NORMALIZE = 1.0 / 32768.0



class Shift(Effect):

    def __init__(self, speed=2.0, dim_time=.1):
        self.speed = speed
        self.dim_time = dim_time
        self.__initstate__()

    def __initstate__(self):
        # state
        try: 
            self._pixel_state
        except AttributeError:
            self._pixel_state = None
        try: 
            self._last_t
        except AttributeError:
            self._last_t = 0.0
        super(Shift, self).__initstate__()

    def numInputChannels(self):
        return 1

    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                # default, min, max, stepsize
                "speed": [2.0, 0.0, 100.0, 0.1],
                "dim_time": [0.1, 0.01, 10.0, 0.01],
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        definition['parameters']['speed'][0] = self.speed
        definition['parameters']['dim_time'][0] = self.dim_time
        return definition

    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            return
        if not self._inputBufferValid(0):
            self._outputBuffer[0] = None
            return

        y = self._inputBuffer[0]
        num_pixels = np.size(y,1)
        if self._pixel_state is None:
            # init with black
            self._pixel_state = np.zeros(num_pixels) * np.array([[0.0],[0.0],[0.0]])
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
    def __init__(self, mode=colors.blend_mode_default):
        self.mode = mode
        self.__initstate__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                "mode": colors.blend_modes
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        definition['parameters']['mode'] = [self.mode] + [x for x in colors.blend_modes if x!=self.mode]
        return definition

    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            return
        if not self._inputBufferValid(0) and not self._inputBufferValid(1):
            # no input on any channels
            self._outputBuffer[0] = None
        elif self._inputBufferValid(0) and self._inputBufferValid(1):
            # input on both channels
            self._outputBuffer[0] = colors.blend(self._inputBuffer[0], self._inputBuffer[1], self.mode)
        elif self._inputBufferValid(0):
            # only channel 0 valid
            self._outputBuffer[0] = self._inputBuffer[0]
        elif self._inputBufferValid(1):
            # only channel 1 valid
            self._outputBuffer[0] = self._inputBuffer[0]
        else:
            self._outputBuffer[0] = None


class AfterGlow(Effect):
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
        super(AfterGlow, self).__initstate__()

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

class Mirror(Effect):

    def __init__(self, mirror_lower = True, recursion = 0):
        self.mirror_lower = mirror_lower
        self.recursion = recursion
        self.__initstate__()

    def __initstate__(self):
        # state
        self._mirrorLower = None 
        self._mirrorUpper = None
        super(Mirror, self).__initstate__()

    def numInputChannels(self):
        return 1

    def numOutputChannels(self):
        return 1

    @staticmethod
    def getParameterDefinition():
        definition = {
            "parameters": {
                "mirror_lower": True,
                # default, min, max, stepsize
                "recursion": [1, 0, 8, 1],
            }
        }
        return definition

    def getParameter(self):
        definition = self.getParameterDefinition()
        definition['parameters']['mirror_lower'] = self.mirror_lower
        definition['parameters']['recursion'][0] = self.recursion
        return definition

    def process(self):
        if self._inputBuffer is None or self._outputBuffer is None:
            return
        if not self._inputBufferValid(0):
            self._outputBuffer[0] = None
            return
        num_pixels = np.size(self._inputBuffer[0], 1)
        if self._mirrorLower is None or np.size(self._mirrorLower,1) != num_pixels:
            self._mirrorLower = self._genMirrorLowerMap(num_pixels,self.recursion)
        if self._mirrorUpper is None or np.size(self._mirrorUpper,1) != num_pixels:
            self._mirrorUpper = self._genMirrorUpperMap(num_pixels,self.recursion)
        buffer = self._inputBuffer[0]
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
