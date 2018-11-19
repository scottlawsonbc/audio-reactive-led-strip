from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import time
import struct
import colorsys
import numpy as np
import audioled.dsp as dsp
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

class InterpolateRGB_gen(Color_gen):
    def __init__(self, num_pixels, colorgen_max, colorgen_min):
        self.colorgen_max = colorgen_max
        self.colorgen_min = colorgen_min
        self.num_pixels = num_pixels
    
    def get_color_array(self, t, num_pixels):
        a = self.colorgen_min.get_color_array(t, num_pixels)
        b = self.colorgen_max.get_color_array(t, num_pixels)
        fact = np.linspace(0., 1., num_pixels)
        return a + np.multiply((b-a), fact)

class InterpolateHSV_gen(Color_gen):
    last_t = -1
    def __init__(self, num_pixels, colorgen_max, colorgen_min):
        self.colorgen_max = colorgen_max
        self.colorgen_min = colorgen_min
        self.num_pixels = num_pixels

    def get_color_array(self, t, num_pixels):
        rgb_a = 1./255. * self.colorgen_min.get_color_array(t, 1)
        rgb_b = 1./255. * self.colorgen_max.get_color_array(t, 1)
        h_a,s_a,v_a = colorsys.rgb_to_hsv(rgb_a[0], rgb_a[1], rgb_a[2])
        h_b,s_b,v_b = colorsys.rgb_to_hsv(rgb_b[0], rgb_b[1], rgb_b[2])

        interp_v = np.linspace(v_a, v_b, num_pixels)
        interp_s = np.linspace(s_a, s_b, num_pixels)
        interp_h = np.linspace(h_a, h_b, num_pixels)
        hsv = np.array([interp_h, interp_s, interp_v]).T
        
        rgb = mpl.colors.hsv_to_rgb(hsv)
        
        return rgb.T * 255.0


