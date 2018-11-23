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
import matplotlib as mpl

class Color_gen(object):
    def __init__(self):
        None
    
    def get_color_array(self, t, num_pixels):
        raise NotImplementedError('get_color_array not implemented')
    
class StaticColor_gen(Color_gen):
    r=0
    g=0
    b=0

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
    
    def get_color_array(self, t, num_pixels):
        return np.ones(num_pixels) * np.array([[self.r],[self.g],[self.b]])

class ColorWheel_gen(Color_gen):

    cycle_time = 30.0
    offset = 0.0

    def __init__(self, cycle_time = 30.0, offset = 0.0):
        self.cycle_time = cycle_time
        self.offset = offset
    
    def get_color(self, t, pixel):
        L=0.5
        S=1.0
        h = (t + self.offset % self.cycle_time) / self.cycle_time
        r, g, b = colorsys.hls_to_rgb(h, L, S) 
        
        return np.array([[r* 255.0], [g* 255.0], [b* 255.0]])
    
    def get_color_array(self, t, num_pixels):
        return np.ones(num_pixels) * self.get_color(t, -1)


class ColorWheel2_gen(Color_gen):
    cycle_time = 30.0
    offset = 0.0
    cycle_time_dim = 10.0

    def __init__(self, cycle_time=30.0, offset=0.0, cycle_time_dim=10.0):
        self.cycle_time = cycle_time
        self.offset = offset
        self.cycle_time_dim = cycle_time_dim

    def get_color(self, t, pixel):
        L = 0.5
        S = 1.0
        dim = math.sin(2 * math.pi / self.cycle_time_dim * t)
        h = (t + self.offset % self.cycle_time) / self.cycle_time
        r, g, b = colorsys.hls_to_rgb(h, L, S)
        CArray = np.array([[dim * r * 255.0], [dim * g * 255.0], [dim * b * 255.0]])

        return CArray

    def get_color_array(self, t, num_pixels):
        return np.ones(num_pixels) * self.get_color(t, -1)





# New Filtergraph Style effects

class StaticColorEffect(filtergraph.Effect):
    def __init__(self, num_pixels, r, g, b):
        self.num_pixels = num_pixels
        self.r = r
        self.g = g
        self.b = b
        self.color = None
        super(StaticColorEffect, self).__init__()
    
    def numInputChannels(self):
        return 0

    def numOutputChannels(self):
        return 1
    
    def setInputBuffer(self, buffer):
        self._inputBuffer = buffer

    def setOutputBuffer(self, buffer):
        self._outputBuffer = buffer
    
    def update(self, dt):
        super(StaticColorEffect, self).update(dt)
        if self.color is None:
            self.color = np.ones(self.num_pixels) * np.array([[self.r],[self.g],[self.b]])

    def process(self):
        self._outputBuffer[0] = self.color

class ColorWheelEffect(filtergraph.Effect):
    """ Generates colors
    """

    def __init__(self, num_pixels = 1, cycle_time = 30.0, offset = 0.0):
        self.cycle_time = cycle_time
        self.offset = offset
        self.num_pixels = num_pixels
        self.color = None
        super(ColorWheelEffect, self).__init__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1

    def update(self, dt):
        super(ColorWheelEffect, self).update(dt)
        self.color = self.get_color_array(self.t, self.num_pixels)

    def process(self):
        if self._outputBuffer is not None:
            self._outputBuffer[0] = self.color

    def get_color(self, t, pixel):
        L=0.5
        S=1
        h = (t + self.offset % self.cycle_time) / self.cycle_time
        r, g, b = colorsys.hls_to_rgb(h, L, S) 
        
        return np.array([[r* 255.0], [g* 255.0], [b* 255.0]])
    
    def get_color_array(self, t, num_pixels):
        return np.ones(num_pixels) * self.get_color(t, -1)


class ColorDimEffect(filtergraph.Effect):
    """ Dim colors, set cycle_time=0 and 0 <  offset < 1 for static dimming
    """

    def __init__(self, num_pixels=1, cycle_time=30.0, offset=0.0):
        self.cycle_time = cycle_time
        self.offset = offset
        self.num_pixels = num_pixels
        self.color = None
        super(ColorDimEffect, self).__init__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1

    def update(self, dt):
        super(ColorDimEffect, self).update(dt)
        self.color = self.get_color_array(self.t, self.num_pixels)

    def process(self):
        if self._outputBuffer is not None:
            self._outputBuffer[0] = self.color

    def get_color(self, t, pixel):
        if self.cycle_time == 0:
            dim = self.offset
        else:
            dim = abs(math.sin((2*math.pi*t / self.cycle_time) + self.offset))

        return np.array([[dim * 255.0], [dim * 255.0], [dim * 255.0]])

    def get_color_array(self, t, num_pixels):
        return np.ones(num_pixels) * self.get_color(t, -1)


class InterpolateRGBEffect(filtergraph.Effect):
    def __init__(self, num_pixels):
        self.num_pixels = num_pixels
        super(InterpolateRGBEffect, self).__init__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1
    
    def process(self):
        if self._inputBuffer is not None and self._outputBuffer is not None:
            a = self._inputBuffer[0]
            b = self._inputBuffer[1]
            if a is not None and b is not None:
                fact = np.linspace(0., 1., self.num_pixels)
                self._outputBuffer[0] = a + np.multiply((b-a), fact)
            elif a is not None:
                self._outputBuffer[0] = a
            elif b is not None:
                self._outputBuffer[0] = b

class InterpolateHSVEffect(filtergraph.Effect):
    def __init__(self, num_pixels):
        self.num_pixels = num_pixels
        super(InterpolateHSVEffect, self).__init__()

    def numInputChannels(self):
        return 2

    def numOutputChannels(self):
        return 1
    
    def process(self):
        if self._inputBuffer is not None and self._outputBuffer is not None:
            a = self._inputBuffer[0]
            b = self._inputBuffer[1]
            
            if a is not None and b is not None:
                rgb_a = 1./255. * a[0:3,0]
                rgb_b = 1./255. * b[0:3,0]
                h_a,s_a,v_a = colorsys.rgb_to_hsv(rgb_a[0], rgb_a[1], rgb_a[2])
                h_b,s_b,v_b = colorsys.rgb_to_hsv(rgb_b[0], rgb_b[1], rgb_b[2])

                interp_v = np.linspace(v_a, v_b, self.num_pixels)
                interp_s = np.linspace(s_a, s_b, self.num_pixels)
                interp_h = np.linspace(h_a, h_b, self.num_pixels)
                hsv = np.array([interp_h, interp_s, interp_v]).T
                
                rgb = mpl.colors.hsv_to_rgb(hsv)
                
                self._outputBuffer[0] = rgb.T * 255.0