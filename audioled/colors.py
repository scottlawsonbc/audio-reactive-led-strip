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

class Color_gen(object):
    def __init__(self):
        None
    
    def get_color(self, t, pixel):
        raise NotImplementedError('get_color not implemented')
    
class StaticColor_gen(Color_gen):
    r=0
    g=0
    b=0

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
    
    def get_color(self, t, pixel):
        return np.array([[self.r],[self.g],[self.b]])

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

class InterpolateRGB_gen(Color_gen):
    def __init__(self, num_pixels, colorgen_max, colorgen_min):
        self.colorgen_max = colorgen_max
        self.colorgen_min = colorgen_min
        self.num_pixels = num_pixels
    
    def get_color(self, t, pixel):
        a = self.colorgen_min.get_color(t, pixel)
        b = self.colorgen_max.get_color(t, pixel)
        frac = float(pixel)/float(self.num_pixels)
        return np.array([
            [a[0] + (b[0] - a[0]) * frac],
            [a[1] + (b[1] - a[1]) * frac],
            [a[2] + (b[2]- a[2]) * frac]])

class InterpolateHSV_gen(Color_gen):
    last_t = -1
    def __init__(self, num_pixels, colorgen_max, colorgen_min):
        self.colorgen_max = colorgen_max
        self.colorgen_min = colorgen_min
        self.num_pixels = num_pixels
    
    def get_color(self, t, pixel):
        if(abs(t-self.last_t) > 1e-10):
            # basic
            rgb_a = 1./255.* self.colorgen_min.get_color(t, pixel)
            rgb_b = 1./255.* self.colorgen_max.get_color(t, pixel)
            h_a,s_a,v_a = colorsys.rgb_to_hsv(rgb_a[0], rgb_a[1], rgb_a[2])
            h_b,s_b,v_b = colorsys.rgb_to_hsv(rgb_b[0], rgb_b[1], rgb_b[2])
            h=0.0
            d = h_b - h_a
            if h_a > h_b:
                h3 = h_b
                h_b = h_a
                h_a = h3
                d = -d
            self.h_a = h_a
            self.s_a = s_a
            self.v_a = v_a
            self.h_b = h_b
            self.s_b = s_b
            self.v_b = v_b
            self.d = d
            self.last_t = t
        

        frac = float(pixel)/float(self.num_pixels)

        if self.h_a > self.h_b:
            frac = 1 - frac
    
        h = 0.0
        h_a = self.h_a
        if self.d > 0.5: # 180deg

            h_a += 1 # 360deg
            h = ( h_a + frac * (self.h_b - h_a) ) % 1 # 360deg
 
        if self.d <= 0.5: # 180deg
 
            h = h_a + frac * self.d

        
        r,g,b = colorsys.hsv_to_rgb(h, self.s_a + frac * (self.s_b-self.s_a), self.v_a + frac * (self.v_b-self.s_b))
        
        return np.array([[r*255.0],[g*255.0],[b*255.0]])