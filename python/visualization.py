from __future__ import print_function
from __future__ import division
from scipy.ndimage.filters import gaussian_filter1d
from collections import deque
import time
import sys
import numpy as np
import config
import microphone
import dsp
import led
if config.USE_GUI:
    from qrangeslider import QRangeSlider
    from qfloatslider import QFloatSlider
    import pyqtgraph as pg
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *

class Visualizer():
    def __init__(self):
        # Dictionary linking names of effects to their respective functions
        self.effects = {"Scroll":self.visualize_scroll,
                        "Energy":self.visualize_energy,
                        "Spectrum":self.visualize_spectrum,
                        #"Power":self.visualize_power,
                        "Wavelength":self.visualize_wavelength,
                        "Beat":self.visualize_beat,
                        "Wave":self.visualize_wave,
                        "Bars":self.visualize_bars,
                        "Single":self.visualize_single,
                        "Fade":self.visualize_fade,
                        "Gradient":self.visualize_gradient}
                        #"Auto":self.visualize_auto}
        # Collection of different colour in RGB format
        self.colors = {"Red":(255,0,0),
                       "Orange":(255,40,0),
                       "Yellow":(255,255,0),
                       "Green":(0,255,0),
                       "Blue":(0,0,255),
                       "Light blue":(1,247,161),
                       "Purple":(80,5,252),
                       "Pink":(255,0,178),
                       "White":(255,255,255)}
        # List of all the visualisation effects that aren't audio reactive.
        # These will still display when no music is playing.
        self.non_reactive_effects = ["Single", "Gradient", "Fade"]
        # List of names of multicolour gradients, used in various effects
        self.multicolor_mode_names = ["Spectral",
                                      "Dancefloor",
                                      "Brilliance",
                                      "Jungle",
                                      "Sky",
                                      "Acid",
                                      "Ocean"]
        # The currently selected effect
        self.current_effect = "Wavelength"
        # Setup for frequency detection algorithm
        self.freq_channel_history = 40
        self.beat_count = 0
        self.freq_channels = [deque(maxlen=self.freq_channel_history) for i in range(config.N_FFT_BINS)]
        self.prev_output = np.array([[0 for i in range(config.N_PIXELS)] for i in range(3)])
        self.prev_spectrum = [0 for i in range(config.N_PIXELS//2)]
        self.current_freq_detects = {"beat":False,
                                     "low":False,
                                     "mid":False,
                                     "high":False}
        self.prev_freq_detects = {"beat":0,
                                  "low":0,
                                  "mid":0,
                                  "high":0}
        self.detection_ranges = {"beat":(0,3),
                                 "low":(3,int(config.N_FFT_BINS*0.2)),
                                 "mid":(int(config.N_FFT_BINS*0.4),int(config.N_FFT_BINS*0.6)),
                                 "high":(int(config.N_FFT_BINS*0.7),int(config.N_FFT_BINS))}
        self.min_detect_amplitude = {"beat":0.7,
                                     "low":0.5,
                                     "mid":0.3,
                                     "high":0.05}
        # Configurable options for effects go in this dictionary.
        # Usage: self.effect_opts[effect][option]
        self.effect_opts = {"Energy":{"blur": 1,                     # Amount of blur to apply
                                      "scale":0.9},                  # Width of effect on strip
                            "Wave":{"color_wave": "Red",             # Colour of moving bit
                                    "color_flash": "White",          # Colour of flashy bit
                                    "wipe_len":5,                    # Initial length of colour bit after beat
                                    "decay": 0.7,                    # How quickly the flash fades away 
                                    "wipe_speed":2},                 # Number of pixels added to colour bit every frame
                            "Wavelength":{"roll_speed": 0,           # How fast (if at all) to cycle colour overlay across strip
                                          "color_mode": "Spectral",  # Colour mode of overlay
                                          "mirror": False,           # Reflect output down centre of strip
                                          "reverse_grad": False,     # Flip (LR) gradient
                                          "reverse_roll": False,     # Reverse movement of gradient roll
                                          "blur": 3.0},              # Amount of blur to apply
                            "Scroll":{"decay": 0.95,                 # How quickly the colour fades away as it moves
                                      "blur": 0.2},                  # Amount of blur to apply
                            "Power":{"blur": 3.0},                   # Amount of blur to apply
                            "Single":{"color": "Red"},               # Static color to show
                            "Beat":{"color": "Red",                  # Colour of beat flash
                                    "decay": 0.7},                   # How quickly the flash fades away
                            "Bars":{"resolution":4,                  # Number of "bars"
                                    "color_mode":"Spectral",         # Multicolour mode to use
                                    "roll_speed":0,                  # How fast (if at all) to cycle colour colours across strip
                                    "mirror": False,                 # Mirror down centre of strip
                                    #"reverse_grad": False,           # Flip (LR) gradient 
                                    "reverse_roll": False},          # Reverse movement of gradient roll
                            "Gradient":{"color_mode":"Spectral",     # Colour gradient to display
                                        "roll_speed": 0,             # How fast (if at all) to cycle colour colours across strip
                                        "mirror": False,             # Mirror gradient down central axis
                                        "reverse": False},           # Reverse movement of gradient
                            "Fade":{"color_mode":"Spectral",         # Colour gradient to fade through
                                    "roll_speed": 1,                 # How fast (if at all) to fade through colours
                                    "reverse": False}                # Reverse "direction" of fade (r->g->b or r<-g<-b)
                            }
        # Configurations for dynamic ui generation. Effect options can be changed by widgets created at runtime,
        # meaning that you don't need to worry about the user interface - it's all done for you. All you need to
        # do is add items to this dict below.
        #
        # First line of code below explained (as an example):
        #   "Energy" is the visualization we're doing options for
        #   "blur" is the key in the options dict (self.effect_opts["Energy"]["blur"])
        #   "Blur" is the string we show on the GUI next to the slider
        #   "float_slider" is the GUI element we want to use
        #   (0.1,4.0,0.1) is a tuple containing all the details for setting up the slider (see above)
        #
        # Each effect key points to a list. Each list contains lists giving config for each option.
        # Syntax: effect:[key, label_text, ui_element, opts]
        #   effect     - the effect which you want to change options for. MUST have a key in self.effect_opts
        #   key        - the key of thing you want to be changed. MUST be in self.effect_opts[effect], otherwise it won't work.
        #   label      - the text displayed on the ui
        #   ui_element - how you want the variable to be changed
        #   opts       - options for the ui element. Must be a tuple.
        # UI Elements + opts:
        #   slider, (min, max, interval)                   (for integer values in a given range)
        #   float_slider, (min, max, interval)             (for floating point values in a given range)
        #   checkbox, ()                                   (for True/False values)
        #   dropdown, (dict or list)                       (dict/list, example see below. Keys will be displayed in the dropdown if dict, otherwise just list items)
        #
        # Hope this clears things up a bit for you! GUI has never been easier..? The reason for doing this is
        # 1 - To make it easy to add options to your effects for the user
        # 2 - To give a consistent GUI for the user. If every options page was set out differently it would all be a mess
        self.dynamic_effects_config = {"Energy":[["blur", "Blur", "float_slider", (0.1,4.0,0.1)],
                                                 ["scale", "Scale", "float_slider", (0.4,1.0,0.05)]],
                                       "Wave":[["color_flash", "Flash Color", "dropdown", self.colors],
                                               ["color_wave", "Wave Color", "dropdown", self.colors],
                                               ["wipe_len", "Wave Start Length", "slider", (0,config.N_PIXELS//4,1)],
                                               ["wipe_speed", "Wave Speed", "slider", (1,10,1)],
                                               ["decay", "Flash Decay", "float_slider", (0.1,1.0,0.05)]],
                                       "Wavelength":[["color_mode", "Color Mode", "dropdown", self.multicolor_mode_names],
                                                     ["roll_speed", "Roll Speed", "slider", (0,8,1)],
                                                     ["blur", "Blur", "float_slider", (0.1,4.0,0.1)],
                                                     ["mirror", "Mirror", "checkbox"],
                                                     ["reverse_grad", "Reverse Gradient", "checkbox"],
                                                     ["reverse_roll", "Reverse Roll", "checkbox"]],
                                       "Scroll":[["blur", "Blur", "float_slider", (0.05,4.0,0.05)],
                                                 ["decay", "Decay", "float_slider", (0.95,1.0,0.005)]],
                                       "Power":[["blur", "Blur", "float_slider", (0.1,4.0,0.1)]],
                                       "Single":[["color", "Color", "dropdown", self.colors]],
                                       "Beat":[["color", "Color", "dropdown", self.colors],
                                               ["decay", "Flash Decay", "float_slider", (0.3,0.98,0.005)]],
                                       "Bars":[["color_mode", "Color Mode", "dropdown", self.multicolor_mode_names],
                                               ["resolution", "Resolution", "slider", (1, config.N_FFT_BINS, 1)],
                                               ["roll_speed", "Roll Speed", "slider", (0,8,1)],
                                               ["mirror", "Mirror", "checkbox"],
                                               ["reverse_roll", "Reverse Roll", "checkbox"]],
                                       "Gradient":[["color_mode", "Color Mode", "dropdown", self.multicolor_mode_names],
                                                   ["roll_speed", "Roll Speed", "slider", (0,8,1)],
                                                   ["mirror", "Mirror", "checkbox"],
                                                   ["reverse", "Reverse", "checkbox"]],
                                       "Fade":[["color_mode", "Color Mode", "dropdown", self.multicolor_mode_names],
                                               ["roll_speed", "Fade Speed", "slider", (0,8,1)],
                                               ["reverse", "Reverse", "checkbox"]]
                                       }
        
        # Setup for "Wave" (don't change these)
        self.wave_wipe_count = 0
        # Setup for multicolour modes (don't mess with this either unless you want to add in your own multicolour modes)
        # If there's a multicolour mode you would like to see, let me know on GitHub! 
        self.multicolor_modes = {}
        # chunks of colour gradients
        _blank_overlay = np.zeros((3,config.N_PIXELS))
        # used to construct rgb overlay. [0-255,255...] whole length of strip
        _gradient_whole = [int(i*255/(config.N_PIXELS//2)) for i in range(config.N_PIXELS//2)] +\
                          [255 for i in range(config.N_PIXELS//2)]
        # also used to make bits and pieces. [0-255], 1/2 length of strip
        _alt_gradient_half = [int(i*255/(config.N_PIXELS//2)) for i in range(config.N_PIXELS//2)]
        # used to construct rgb overlay. [0-255,255...] 1/2 length of strip
        _gradient_half = _gradient_whole[::2]
        # Spectral colour mode
        self.multicolor_modes["Spectral"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Spectral"][2, :config.N_PIXELS//2] = _gradient_half[::-1]
        self.multicolor_modes["Spectral"][1, :] = _gradient_half + _gradient_half[::-1]
        self.multicolor_modes["Spectral"][0, :] = np.flipud(self.multicolor_modes["Spectral"][2])
        # Dancefloor colour mode
        self.multicolor_modes["Dancefloor"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Dancefloor"][2, :] = _gradient_whole[::-1]
        self.multicolor_modes["Dancefloor"][0, :] = _gradient_whole
        # Brilliance colour mode
        self.multicolor_modes["Brilliance"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Brilliance"][2, :] = _gradient_whole[::-1]
        self.multicolor_modes["Brilliance"][1, :] = 255
        self.multicolor_modes["Brilliance"][0, :] = _gradient_whole
        # Jungle colour mode
        self.multicolor_modes["Jungle"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Jungle"][1, :] = _gradient_whole[::-1]
        self.multicolor_modes["Jungle"][0, :] = _gradient_whole
        # Sky colour mode
        self.multicolor_modes["Sky"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Sky"][1, :config.N_PIXELS//2] = _alt_gradient_half[::-1]
        self.multicolor_modes["Sky"][0, config.N_PIXELS//2:] = _alt_gradient_half
        self.multicolor_modes["Sky"][2, :] = 255
        # Acid colour mode
        self.multicolor_modes["Acid"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Acid"][2, :config.N_PIXELS//2] = _alt_gradient_half[::-1]
        self.multicolor_modes["Acid"][1, :] = 255
        self.multicolor_modes["Acid"][0, config.N_PIXELS//2:] = _alt_gradient_half
        # Ocean colour mode
        self.multicolor_modes["Ocean"] = np.zeros((3,config.N_PIXELS))
        self.multicolor_modes["Ocean"][1, :] = _gradient_whole
        self.multicolor_modes["Ocean"][2, :] = _gradient_whole[::-1]
        for i in self.multicolor_modes:
            self.multicolor_modes[i] = np.concatenate((self.multicolor_modes[i][:, ::-1],
                                                       self.multicolor_modes[i]), axis=1)

    def get_vis(self, y, audio_input):
        self.update_freq_channels(y)
        self.detect_freqs()
        if audio_input:
            self.prev_output = np.copy(self.effects[self.current_effect](y))
        elif self.current_effect in self.non_reactive_effects:
            self.prev_output = np.copy(self.effects[self.current_effect](y))
        else:
            self.prev_output = np.multiply(self.prev_output, 0.95)
        return self.prev_output

    def _split_equal(self, value, parts):
        value = float(value)
        return [int(round(i*value/parts)) for i in range(1,parts+1)]

    def update_freq_channels(self, y):
        for i in range(len(y)):
            self.freq_channels[i].appendleft(y[i])

    def detect_freqs(self):
        """
        Function that updates current_freq_detects. Any visualisation algorithm can check if
        there is currently a beat, low, mid, or high by querying the self.current_freq_detects dict.
        """
        channel_avgs = []
        differences = []
        for i in range(config.N_FFT_BINS):
            channel_avgs.append(sum(self.freq_channels[i])/len(self.freq_channels[i]))
            differences.append(((self.freq_channels[i][0]-channel_avgs[i])*100)//channel_avgs[i])
        for i in ["beat", "low", "mid", "high"]:
            if any(differences[j] >= 100 and self.freq_channels[j][0] >= self.min_detect_amplitude[i]\
                        for j in range(*self.detection_ranges[i]))\
                    and (time.time() - self.prev_freq_detects[i] > 0.15)\
                    and len(self.freq_channels[0]) == self.freq_channel_history:
                self.prev_freq_detects[i] = time.time()
                self.current_freq_detects[i] = True
                #print(i)
            else:
                self.current_freq_detects[i] = False                

    def visualize_scroll(self, y):
        """Effect that originates in the center and scrolls outwards"""
        global p
        y = y**2.0
        gain.update(y)
        y /= gain.value
        y *= 255.0
        r = int(np.max(y[:len(y) // 3]))
        g = int(np.max(y[len(y) // 3: 2 * len(y) // 3]))
        b = int(np.max(y[2 * len(y) // 3:]))
        # Scrolling effect window
        p[:, 1:] = p[:, :-1]
        p *= self.effect_opts["Scroll"]["decay"]
        p = gaussian_filter1d(p, sigma=self.effect_opts["Scroll"]["blur"])
        # Create new color originating at the center
        p[0, 0] = r
        p[1, 0] = g
        p[2, 0] = b
        # Update the LED strip
        return np.concatenate((p[:, ::-1], p), axis=1)


    def visualize_energy(self, y):
        """Effect that expands from the center with increasing sound energy"""
        global p
        y = np.copy(y)
        gain.update(y)
        y /= gain.value
        scale = self.effect_opts["Energy"]["scale"]
        # Scale by the width of the LED strip
        y *= float((config.N_PIXELS * scale) - 1)
        # Map color channels according to energy in the different freq bands
        r = int(np.mean(y[:len(y) // 3]**scale))
        g = int(np.mean(y[len(y) // 3: 2 * len(y) // 3]**scale))
        b = int(np.mean(y[2 * len(y) // 3:]**scale))
        # Assign color to different frequency regions
        p[0, :r] = 255.0
        p[0, r:] = 0.0
        p[1, :g] = 255.0
        p[1, g:] = 0.0
        p[2, :b] = 255.0
        p[2, b:] = 0.0
        p_filt.update(p)
        p = np.round(p_filt.value)
        # Apply blur to smooth the edges
        p[0, :] = gaussian_filter1d(p[0, :], sigma=self.effect_opts["Energy"]["blur"])
        p[1, :] = gaussian_filter1d(p[1, :], sigma=self.effect_opts["Energy"]["blur"])
        p[2, :] = gaussian_filter1d(p[2, :], sigma=self.effect_opts["Energy"]["blur"])
        # Set the new pixel value
        return np.concatenate((p[:, ::-1], p), axis=1)

    def visualize_wavelength(self, y):
        y = np.copy(interpolate(y, config.N_PIXELS // 2))
        common_mode.update(y)
        diff = y - self.prev_spectrum
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = r_filt.update(y - common_mode.value)
        #g = np.abs(diff)
        b = b_filt.update(np.copy(y))
        r = np.array([j for i in zip(r,r) for j in i])
        output = np.array([self.multicolor_modes[self.effect_opts["Wavelength"]["color_mode"]][0][
                                    (config.N_PIXELS if self.effect_opts["Wavelength"]["reverse_grad"] else 0):
                                    (None if self.effect_opts["Wavelength"]["reverse_grad"] else config.N_PIXELS):]*r,
                           self.multicolor_modes[self.effect_opts["Wavelength"]["color_mode"]][1][
                                    (config.N_PIXELS if self.effect_opts["Wavelength"]["reverse_grad"] else 0):
                                    (None if self.effect_opts["Wavelength"]["reverse_grad"] else config.N_PIXELS):]*r,
                           self.multicolor_modes[self.effect_opts["Wavelength"]["color_mode"]][2][
                                    (config.N_PIXELS if self.effect_opts["Wavelength"]["reverse_grad"] else 0):
                                    (None if self.effect_opts["Wavelength"]["reverse_grad"] else config.N_PIXELS):]*r])
        #self.prev_spectrum = y
        self.multicolor_modes[self.effect_opts["Wavelength"]["color_mode"]] = np.roll(
                    self.multicolor_modes[self.effect_opts["Wavelength"]["color_mode"]],
                    self.effect_opts["Wavelength"]["roll_speed"]*(-1 if self.effect_opts["Wavelength"]["reverse_roll"] else 1),
                    axis=1)
        output[0] = gaussian_filter1d(output[0], sigma=self.effect_opts["Wavelength"]["blur"])
        output[1] = gaussian_filter1d(output[1], sigma=self.effect_opts["Wavelength"]["blur"])
        output[2] = gaussian_filter1d(output[2], sigma=self.effect_opts["Wavelength"]["blur"])
        if self.effect_opts["Wavelength"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output

    def visualize_power(self, y):
        """Effect that pulses different reqions of the strip increasing sound energy"""
        global p
        _p = np.copy(p)
        y = np.copy(interpolate(y, config.N_PIXELS // 2))
        common_mode.update(y)
        diff = y - self.prev_spectrum
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = r_filt.update(y - common_mode.value)
        g = np.abs(diff)
        b = b_filt.update(np.copy(y))
        # I have no idea what any of this does but it looks kinda cool
        r = [int(i*255) for i in r[::3]]
        g = [int(i*255) for i in g[::3]]
        b = [int(i*255) for i in b[::3]]
        _p[0, 0:len(r)] = r
        _p[1, len(r):len(r)+len(g)] = g
        _p[2, len(r)+len(g):config.N_PIXELS] = b[:39] # this needs to be fixed 
        p_filt.update(_p)
        # Clip it into range
        _p = np.clip(p, 0, 255).astype(int)
        # Apply substantial blur to smooth the edges
        _p[0, :] = gaussian_filter1d(_p[0, :], sigma=self.effect_opts["Power"]["blur"])
        _p[1, :] = gaussian_filter1d(_p[1, :], sigma=self.effect_opts["Power"]["blur"])
        _p[2, :] = gaussian_filter1d(_p[2, :], sigma=self.effect_opts["Power"]["blur"])
        self.prev_spectrum = y
        return np.concatenate((_p[:, ::-1], _p), axis=1)
    
    def visualize_spectrum(self, y):
        """Effect that maps the Mel filterbank frequencies onto the LED strip"""
        global p
        #print(len(y))
        #print(y)
        y = np.copy(interpolate(y, config.N_PIXELS // 2))
        common_mode.update(y)
        diff = y - self.prev_spectrum
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = r_filt.update(y - common_mode.value)
        g = np.abs(diff)
        b = b_filt.update(np.copy(y))
        # Mirror the color channels for symmetric output
        r = np.concatenate((r[::-1], r))
        g = np.concatenate((g[::-1], g))
        b = np.concatenate((b[::-1], b))
        output = np.array([r, g,b]) * 255
        self.prev_spectrum = y
        return output

    def visualize_auto(self,y):
        """Automatically (intelligently?) cycle through effects"""
        return self.visualize_beat(y) # real intelligent

    def visualize_wave(self, y):
        """Effect that flashes to the beat with scrolling coloured bits"""
        if self.current_freq_detects["beat"]:
            output = np.zeros((3,config.N_PIXELS))
            output[0][:]=self.colors[self.effect_opts["Wave"]["color_flash"]][0]
            output[1][:]=self.colors[self.effect_opts["Wave"]["color_flash"]][1]
            output[2][:]=self.colors[self.effect_opts["Wave"]["color_flash"]][2]
            self.wave_wipe_count = self.effect_opts["Wave"]["wipe_len"]
        else:
            output = np.copy(self.prev_output)
            #for i in range(len(self.prev_output)):
            #    output[i] = np.hsplit(self.prev_output[i],2)[0]
            output = np.multiply(self.prev_output,self.effect_opts["Wave"]["decay"])
            for i in range(self.wave_wipe_count):
                output[0][i]=self.colors[self.effect_opts["Wave"]["color_wave"]][0]
                output[0][-i]=self.colors[self.effect_opts["Wave"]["color_wave"]][0]
                output[1][i]=self.colors[self.effect_opts["Wave"]["color_wave"]][1]
                output[1][-i]=self.colors[self.effect_opts["Wave"]["color_wave"]][1]
                output[2][i]=self.colors[self.effect_opts["Wave"]["color_wave"]][2]
                output[2][-i]=self.colors[self.effect_opts["Wave"]["color_wave"]][2]
            #output = np.concatenate([output,np.fliplr(output)], axis=1)
            self.wave_wipe_count += self.effect_opts["Wave"]["wipe_speed"]
            if self.wave_wipe_count > config.N_PIXELS//2:
                self.wave_wipe_count = config.N_PIXELS//2
        return output

    def visualize_beat(self, y):
        """Effect that flashes to the beat"""
        if self.current_freq_detects["beat"]:
            output = np.zeros((3,config.N_PIXELS))
            output[0][:]=self.colors[self.effect_opts["Beat"]["color"]][0]
            output[1][:]=self.colors[self.effect_opts["Beat"]["color"]][1]
            output[2][:]=self.colors[self.effect_opts["Beat"]["color"]][2]
        else:
            output = np.copy(self.prev_output)
            output = np.multiply(self.prev_output,self.effect_opts["Beat"]["decay"])
        return output

    def visualize_bars(self, y):
        # Bit of fiddling with the y values
        y = np.copy(interpolate(y, config.N_PIXELS // 2))
        common_mode.update(y)
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = r_filt.update(y - common_mode.value)
        r = np.array([j for i in zip(r,r) for j in i])
        # Split y into [resulution] chunks and calculate the average of each
        max_values = np.array([max(i) for i in np.array_split(r, self.effect_opts["Bars"]["resolution"])])
        max_values = np.clip(max_values, 0, 1)
        color_sets = []
        for i in range(self.effect_opts["Bars"]["resolution"]):
            # [r,g,b] values from a multicolour gradient array at [resulution] equally spaced intervals
            color_sets.append([self.multicolor_modes[self.effect_opts["Bars"]["color_mode"]]\
                              [j][i*(config.N_PIXELS//self.effect_opts["Bars"]["resolution"])] for j in range(3)])
        output = np.zeros((3,config.N_PIXELS))
        chunks = np.array_split(output[0], self.effect_opts["Bars"]["resolution"])
        n = 0
        # Assign blocks with heights corresponding to max_values and colours from color_sets
        for i in range(len(chunks)):
            m = len(chunks[i])
            for j in range(3):
                output[j][n:n+m] = color_sets[i][j]*max_values[i]
            n += m
        self.multicolor_modes[self.effect_opts["Bars"]["color_mode"]] = np.roll(
                    self.multicolor_modes[self.effect_opts["Bars"]["color_mode"]],
                    self.effect_opts["Bars"]["roll_speed"]*(-1 if self.effect_opts["Bars"]["reverse_roll"] else 1),
                    axis=1)
        if self.effect_opts["Bars"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output

        
        

    def visualize_single(self, y):
        "Displays a single colour, non audio reactive"
        output = np.zeros((3,config.N_PIXELS))
        output[0][:]=self.colors[self.effect_opts["Single"]["color"]][0]
        output[1][:]=self.colors[self.effect_opts["Single"]["color"]][1]
        output[2][:]=self.colors[self.effect_opts["Single"]["color"]][2]
        return output

    def visualize_gradient(self, y):
        "Displays a multicolour gradient, non audio reactive"
        output = np.array([self.multicolor_modes[self.effect_opts["Gradient"]["color_mode"]][0][:config.N_PIXELS],
                           self.multicolor_modes[self.effect_opts["Gradient"]["color_mode"]][1][:config.N_PIXELS],
                           self.multicolor_modes[self.effect_opts["Gradient"]["color_mode"]][2][:config.N_PIXELS]])
        self.multicolor_modes[self.effect_opts["Gradient"]["color_mode"]] = np.roll(
                           self.multicolor_modes[self.effect_opts["Gradient"]["color_mode"]],
                           self.effect_opts["Gradient"]["roll_speed"]*(-1 if self.effect_opts["Gradient"]["reverse"] else 1),
                           axis=1)
        if self.effect_opts["Gradient"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output

    def visualize_fade(self, y):
        "Fades through a multicolour gradient, non audio reactive"
        output = [[self.multicolor_modes[self.effect_opts["Fade"]["color_mode"]][0][0] for i in range(config.N_PIXELS)],
                  [self.multicolor_modes[self.effect_opts["Fade"]["color_mode"]][1][0] for i in range(config.N_PIXELS)],
                  [self.multicolor_modes[self.effect_opts["Fade"]["color_mode"]][2][0] for i in range(config.N_PIXELS)]]
        self.multicolor_modes[self.effect_opts["Fade"]["color_mode"]] = np.roll(
                           self.multicolor_modes[self.effect_opts["Fade"]["color_mode"]],
                           self.effect_opts["Fade"]["roll_speed"]*(-1 if self.effect_opts["Fade"]["reverse"] else 1),
                           axis=1)
        return output
        
class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # ==================================== Set up window and wrapping layout
        self.setWindowTitle("Visualization")
        wrapper = QVBoxLayout()

        # ========================================== Set up FPS and error labels
        labels_layout = QHBoxLayout()
        self.label_error = QLabel("")
        self.label_fps = QLabel("")
        self.label_fps.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        labels_layout.addWidget(self.label_error)
        labels_layout.addStretch()
        labels_layout.addWidget(self.label_fps)
        
        # ================================================== Set up graph layout
        graph_view = pg.GraphicsView()
        graph_layout = pg.GraphicsLayout(border=(100,100,100))
        graph_view.setCentralItem(graph_layout)
        # Mel filterbank plot
        fft_plot = graph_layout.addPlot(title='Filterbank Output', colspan=3)
        fft_plot.setRange(yRange=[-0.1, 1.2])
        fft_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        x_data = np.array(range(1, config.N_FFT_BINS + 1))
        self.mel_curve = pg.PlotCurveItem()
        self.mel_curve.setData(x=x_data, y=x_data*0)
        fft_plot.addItem(self.mel_curve)
        # Visualization plot
        graph_layout.nextRow()
        led_plot = graph_layout.addPlot(title='Visualization Output', colspan=3)
        led_plot.setRange(yRange=[-5, 260])
        led_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        # Pen for each of the color channel curves
        r_pen = pg.mkPen((255, 30, 30, 200), width=4)
        g_pen = pg.mkPen((30, 255, 30, 200), width=4)
        b_pen = pg.mkPen((30, 30, 255, 200), width=4)
        # Color channel curves
        self.r_curve = pg.PlotCurveItem(pen=r_pen)
        self.g_curve = pg.PlotCurveItem(pen=g_pen)
        self.b_curve = pg.PlotCurveItem(pen=b_pen)
        # Define x data
        x_data = np.array(range(1, config.N_PIXELS + 1))
        self.r_curve.setData(x=x_data, y=x_data*0)
        self.g_curve.setData(x=x_data, y=x_data*0)
        self.b_curve.setData(x=x_data, y=x_data*0)
        # Add curves to plot
        led_plot.addItem(self.r_curve)
        led_plot.addItem(self.g_curve)
        led_plot.addItem(self.b_curve)

        # ================================================= Set up button layout
        label_reactive = QLabel("Audio Reactive Effects")
        label_non_reactive = QLabel("Non Reactive Effects")
        reactive_button_grid = QGridLayout()
        non_reactive_button_grid = QGridLayout()        
        buttons = {}
        connecting_funcs = {}
        grid_width = 4
        i = 0
        j = 0
        k = 0
        l = 0
        # Dynamically layout reactive_buttons and connect them to the visualisation effects
        def connect_generator(effect):
            def func():
                visualizer.current_effect = effect
                buttons[effect].setDown(True)
            func.__name__ = effect
            return func
        # Where the magic happens
        for effect in visualizer.effects:
            if not effect in visualizer.non_reactive_effects:
                connecting_funcs[effect] = connect_generator(effect)
                buttons[effect] = QPushButton(effect)
                buttons[effect].clicked.connect(connecting_funcs[effect])
                reactive_button_grid.addWidget(buttons[effect], j, i)
                i += 1
                if i % grid_width == 0:
                    i = 0
                    j += 1
            else:
                connecting_funcs[effect] = connect_generator(effect)
                buttons[effect] = QPushButton(effect)
                buttons[effect].clicked.connect(connecting_funcs[effect])
                non_reactive_button_grid.addWidget(buttons[effect], l, k)
                k += 1
                if k % grid_width == 0:
                    k = 0
                    l += 1
                
        # ============================================== Set up frequency slider
        # Frequency range label
        label_slider = QLabel("Frequency Range")
        # Frequency slider
        def freq_slider_change(tick):
            minf = freq_slider.tickValue(0)**2.0 * (config.MIC_RATE / 2.0)
            maxf = freq_slider.tickValue(1)**2.0 * (config.MIC_RATE / 2.0)
            t = 'Frequency range: {:.0f} - {:.0f} Hz'.format(minf, maxf)
            freq_label.setText(t)
            config.MIN_FREQUENCY = minf
            config.MAX_FREQUENCY = maxf
            dsp.create_mel_bank()
        def set_freq_min():
            config.MIN_FREQUENCY = freq_slider.start()
            dsp.create_mel_bank()
        def set_freq_max():
            config.MAX_FREQUENCY = freq_slider.end()
            dsp.create_mel_bank()
        freq_slider = QRangeSlider()
        freq_slider.show()
        freq_slider.setMin(0)
        freq_slider.setMax(20000)
        freq_slider.setRange(config.MIN_FREQUENCY, config.MAX_FREQUENCY)
        freq_slider.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        freq_slider.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')
        freq_slider.setDrawValues(True)
        freq_slider.endValueChanged.connect(set_freq_max)
        freq_slider.startValueChanged.connect(set_freq_min)
        freq_slider.setStyleSheet("""
        QRangeSlider * {
            border: 0px;
            padding: 0px;
        }
        QRangeSlider > QSplitter::handle {
            background: #fff;
        }
        QRangeSlider > QSplitter::handle:vertical {
            height: 3px;
        }
        QRangeSlider > QSplitter::handle:pressed {
            background: #ca5;
        }
        """)

        # ============================================ Set up option tabs layout
        label_options = QLabel("Effect Options")
        opts_tabs = QTabWidget()
        # Dynamically set up tabs
        tabs = {}
        grid_layouts = {}
        self.grid_layout_widgets = {}
        options = visualizer.effect_opts.keys()
        for effect in visualizer.effects:
            # Make the tab
            self.grid_layout_widgets[effect] = {}
            tabs[effect] = QWidget()
            grid_layouts[effect] = QGridLayout()
            tabs[effect].setLayout(grid_layouts[effect])
            opts_tabs.addTab(tabs[effect],effect)
            # These functions make functions for the dynamic ui generation
            # YOU WANT-A DYNAMIC I GIVE-A YOU DYNAMIC!
            def gen_slider_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].value()
                return func
            def gen_float_slider_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].slider_value
                return func
            def gen_combobox_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].currentText()
                return func
            def gen_checkbox_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].isChecked()
                return func
            # Dynamically generate ui for settings
            if effect in visualizer.dynamic_effects_config:
                i = 0
                connecting_funcs[effect] = {}
                for key, label, ui_element, *opts in visualizer.dynamic_effects_config[effect]:
                    if opts: # neatest way  ^^^^^ i could think of to unpack and handle an unknown number of opts (if any)
                        opts = opts[0]
                    if ui_element == "slider":
                        connecting_funcs[effect][key] = gen_slider_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QSlider(Qt.Horizontal)
                        self.grid_layout_widgets[effect][key].setMinimum(opts[0])
                        self.grid_layout_widgets[effect][key].setMaximum(opts[1])
                        self.grid_layout_widgets[effect][key].setValue(visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].valueChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "float_slider":
                        connecting_funcs[effect][key] = gen_float_slider_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QFloatSlider(*opts, visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].setValue(visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].valueChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "dropdown":
                        connecting_funcs[effect][key] = gen_combobox_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QComboBox()
                        self.grid_layout_widgets[effect][key].addItems(opts)
                        self.grid_layout_widgets[effect][key].currentIndexChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "checkbox":
                        connecting_funcs[effect][key] = gen_checkbox_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QCheckBox()
                        self.grid_layout_widgets[effect][key].setCheckState(visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].stateChanged.connect(
                                connecting_funcs[effect][key])
                    grid_layouts[effect].addWidget(QLabel(label),i,0)
                    grid_layouts[effect].addWidget(self.grid_layout_widgets[effect][key],i,1)
                    i += 1    
                #visualizer.effect_settings[effect]
            else:
                grid_layouts[effect].addWidget(QLabel("No customisable options for this effect :("),0,0)
                
        
        
        # ============================================= Add layouts into wrapper
        self.setLayout(wrapper)
        wrapper.addLayout(labels_layout)
        wrapper.addWidget(graph_view)
        wrapper.addWidget(label_reactive)
        wrapper.addLayout(reactive_button_grid)
        wrapper.addWidget(label_non_reactive)
        wrapper.addLayout(non_reactive_button_grid)
        wrapper.addWidget(label_slider)
        wrapper.addWidget(freq_slider)
        wrapper.addWidget(label_options)
        wrapper.addWidget(opts_tabs)
        self.show()


def frames_per_second():
    """Return the estimated frames per second

    Returns the current estimate for frames-per-second (FPS).
    FPS is estimated by measured the amount of time that has elapsed since
    this function was previously called. The FPS estimate is low-pass filtered
    to reduce noise.

    This function is intended to be called one time for every iteration of
    the program's main loop.

    Returns
    -------
    fps : float
        Estimated frames-per-second. This value is low-pass filtered
        to reduce noise.
    """
    global _time_prev, _fps
    time_now = time.time() * 1000.0
    dt = time_now - _time_prev
    _time_prev = time_now
    if dt == 0.0:
        return _fps.value
    return _fps.update(1000.0 / dt)

def memoize(function):
    """Provides a decorator for memoizing functions"""
    from functools import wraps
    memo = {}

    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper

@memoize
def _normalized_linspace(size):
    return np.linspace(0, 1, size)

def interpolate(y, new_length):
    """Intelligently resizes the array by linearly interpolating the values

    Parameters
    ----------
    y : np.array
        Array that should be resized

    new_length : int
        The length of the new interpolated array

    Returns
    -------
    z : np.array
        New array with length of new_length that contains the interpolated
        values of y.
    """
    if len(y) == new_length:
        return y
    x_old = _normalized_linspace(len(y))
    x_new = _normalized_linspace(new_length)
    z = np.interp(x_new, x_old, y)
    return z

def microphone_update(audio_samples):
    global y_roll, prev_rms, prev_exp, prev_fps_update
    # Normalize samples between 0 and 1
    y = audio_samples / 2.0**15
    # Construct a rolling window of audio samples
    y_roll[:-1] = y_roll[1:]
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0).astype(np.float32)
    vol = np.max(np.abs(y_data))
    # Transform audio input into the frequency domain
    N = len(y_data)
    N_zeros = 2**int(np.ceil(np.log2(N))) - N
    # Pad with zeros until the next power of two
    y_data *= fft_window
    y_padded = np.pad(y_data, (0, N_zeros), mode='constant')
    YS = np.abs(np.fft.rfft(y_padded)[:N // 2])
    # Construct a Mel filterbank from the FFT data
    mel = np.atleast_2d(YS).T * dsp.mel_y.T
    # Scale data to values more suitable for visualization
    mel = np.sum(mel, axis=0)
    mel = mel**0.8
    # Gain normalization
    mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
    mel /= mel_gain.value
    mel = mel_smoothing.update(mel)
    # Map filterbank output onto LED strip
    led.pixels = visualizer.get_vis(mel, audio_input = True if vol > config.MIN_VOLUME_THRESHOLD else False)
    led.update()
    if config.USE_GUI:
        x = np.linspace(config.MIN_FREQUENCY, config.MAX_FREQUENCY, len(mel))
        if vol < config.MIN_VOLUME_THRESHOLD:
            gui.label_error.setText("No audio input. Volume below threshold.")
            gui.mel_curve.setData(x=x, y=[0 for i in range(config.N_FFT_BINS)])
        else:
            # Plot filterbank output
            gui.mel_curve.setData(x=x, y=fft_plot_filter.update(mel))
            gui.label_error.setText("")
        fps = frames_per_second()
        if time.time() - 0.5 > prev_fps_update:
            prev_fps_update = time.time()
        app.processEvents()
        # Plot the color channels
        gui.r_curve.setData(y=led.pixels[0])
        gui.g_curve.setData(y=led.pixels[1])
        gui.b_curve.setData(y=led.pixels[2])
        # Update fps counter
        gui.label_fps.setText('{:.0f} / {:.0f} FPS'.format(fps, config.FPS))
    elif vol < config.MIN_VOLUME_THRESHOLD:
        print("No audio input. Volume below threshold. Volume: {}".format(vol))
    if config.DISPLAY_FPS:
        print('FPS {:.0f} / {:.0f}'.format(fps, config.FPS))
        
# Initialise visualiser and GUI
visualizer = Visualizer()
if config.USE_GUI:
    # Create GUI window
    app = QApplication([])
    app.setApplicationName('Visualization')
    gui = GUI()
    app.processEvents()

# Initialise filter stuff
fft_plot_filter = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.5, alpha_rise=0.99)
mel_gain = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.01, alpha_rise=0.99)
mel_smoothing = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.5, alpha_rise=0.99)
volume = dsp.ExpFilter(config.MIN_VOLUME_THRESHOLD,
                       alpha_decay=0.02, alpha_rise=0.02)
fft_window = np.hamming(int(config.MIC_RATE / config.FPS) * config.N_ROLLING_HISTORY)
prev_fps_update = time.time()

# Initialise more filter stuff
r_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.2, alpha_rise=0.99)
g_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.05, alpha_rise=0.3)
b_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.1, alpha_rise=0.5)
common_mode = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.99, alpha_rise=0.01)
p_filt = dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99)
p = np.tile(1.0, (3, config.N_PIXELS // 2))
gain = dsp.ExpFilter(np.tile(0.01, config.N_FFT_BINS),
                     alpha_decay=0.001, alpha_rise=0.99)

# The previous time that the frames_per_second() function was called
_time_prev = time.time() * 1000.0
# The low-pass filter used to estimate frames-per-second
_fps = dsp.ExpFilter(val=config.FPS, alpha_decay=0.2, alpha_rise=0.2)


# Number of audio samples to read every time frame
samples_per_frame = int(config.MIC_RATE / config.FPS)
# Array containing the rolling audio sample window
y_roll = np.random.rand(config.N_ROLLING_HISTORY, samples_per_frame) / 1e16
# Initialize LEDs
led.update()
# Start listening to live audio stream
microphone.start_stream(microphone_update)
