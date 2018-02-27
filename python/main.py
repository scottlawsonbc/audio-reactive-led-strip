from __future__ import print_function
from __future__ import division
from scipy.ndimage.filters import gaussian_filter1d
from collections import deque
import time
import sys
import numpy as np
import lib.config  as config
import lib.microphone as microphone
import lib.dsp as dsp
#import lib.led as led
import lib.melbank as melbank
import lib.devices as devices
import random
from PyQt5.QtCore import QSettings
if config.settings["configuration"]["USE_GUI"]:
    from lib.qrangeslider import QRangeSlider
    from lib.qfloatslider import QFloatSlider
    import pyqtgraph as pg
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *

class Visualizer():
    def __init__(self, board):
        # Name of board this for which this visualizer instance is visualising
        self.board = board
        # Dictionary linking names of effects to their respective functions
        self.effects = {"Scroll":self.visualize_scroll,
                        "Energy":self.visualize_energy,
                        "Spectrum":self.visualize_spectrum,
                        "Power":self.visualize_power,
                        "Wavelength":self.visualize_wavelength,
                        "Beat":self.visualize_beat,
                        "Wave":self.visualize_wave,
                        "Bars":self.visualize_bars,
                        #"Pulse":self.visualize_pulse,
                        #"Auto":self.visualize_auto,
                        "Single":self.visualize_single,
                        "Fade":self.visualize_fade,
                        "Gradient":self.visualize_gradient,
                        "Calibration": self.visualize_calibration}
        # List of all the visualisation effects that aren't audio reactive.
        # These will still display when no music is playing.
        self.non_reactive_effects = ["Single", "Gradient", "Fade", "Calibration"]
        # Setup for frequency detection algorithm
        self.freq_channel_history = 40
        self.beat_count = 0
        self.freq_channels = [deque(maxlen=self.freq_channel_history) for i in range(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"])]
        self.prev_output = np.array([[0 for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])] for i in range(3)])
        self.prev_spectrum = [0 for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2)]
        self.current_freq_detects = {"beat":False,
                                     "low":False,
                                     "mid":False,
                                     "high":False}
        self.prev_freq_detects = {"beat":0,
                                  "low":0,
                                  "mid":0,
                                  "high":0}
        self.detection_ranges = {"beat":(0,int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.13)),
                                 "low":(int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.15),
                                        int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.4)),
                                 "mid":(int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.4),
                                        int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.7)),
                                 "high":(int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.8),
                                         int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]))}
        self.min_detect_amplitude = {"beat":0.7,
                                     "low":0.5,
                                     "mid":0.3,
                                     "high":0.3}
        self.min_percent_diff = {"beat":70,
                                 "low":100,
                                 "mid":50,
                                 "high":30}
        # Configurations for dynamic ui generation. Effect options can be changed by widgets created at runtime,
        # meaning that you don't need to worry about the user interface - it's all done for you. All you need to
        # do is add items to this dict below.
        #
        # First line of code below explained (as an example):
        #   "Energy" is the visualization we're doing options for
        #   "blur" is the key in the options dict (config.settings["devices"][self.board]["effect_opts"]["Energy"]["blur"])
        #   "Blur" is the string we show on the GUI next to the slider
        #   "float_slider" is the GUI element we want to use
        #   (0.1,4.0,0.1) is a tuple containing all the details for setting up the slider (see above)
        #
        # Each effect key points to a list. Each list contains lists giving config for each option.
        # Syntax: effect:[key, label_text, ui_element, opts]
        #   effect     - the effect which you want to change options for. MUST have a key in config.settings["devices"][self.board]["effect_opts"]
        #   key        - the key of thing you want to be changed. MUST be in config.settings["devices"][self.board]["effect_opts"][effect], otherwise it won't work.
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
                                                 ["scale", "Scale", "float_slider", (0.4,1.0,0.05)],
                                                 ["r_multiplier", "Red", "float_slider", (0.05,1.0,0.05)],
                                                 ["g_multiplier", "Green", "float_slider", (0.05,1.0,0.05)],
                                                 ["b_multiplier", "Blue", "float_slider", (0.05,1.0,0.05)]],
                                         "Wave":[["color_flash", "Flash Color", "dropdown", config.settings["colors"]],
                                                 ["color_wave", "Wave Color", "dropdown", config.settings["colors"]],
                                                 ["wipe_len", "Wave Start Length", "slider", (0,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//4,1)],
                                                 ["wipe_speed", "Wave Speed", "slider", (1,10,1)],
                                                 ["decay", "Flash Decay", "float_slider", (0.1,1.0,0.05)]],
                                     "Spectrum":[["r_multiplier", "Red", "float_slider", (0.05,1.0,0.05)],
                                                 ["g_multiplier", "Green", "float_slider", (0.05,1.0,0.05)],
                                                 ["b_multiplier", "Blue", "float_slider", (0.05,1.0,0.05)]],
                                   "Wavelength":[["color_mode", "Color Mode", "dropdown", config.settings["gradients"]],
                                                 ["roll_speed", "Roll Speed", "slider", (0,8,1)],
                                                 ["blur", "Blur", "float_slider", (0.1,4.0,0.1)],
                                                 ["mirror", "Mirror", "checkbox"],
                                                 ["reverse_grad", "Reverse Gradient", "checkbox"],
                                                 ["reverse_roll", "Reverse Roll", "checkbox"],
                                                 ["flip_lr", "Flip LR", "checkbox"]],
                                       "Scroll":[["blur", "Blur", "float_slider", (0.05,4.0,0.05)],
                                                 ["decay", "Decay", "float_slider", (0.97,1.0,0.0005)],
                                                 ["speed", "Speed", "slider", (1,5,1)],
                                                 ["r_multiplier", "Red", "float_slider", (0.05,1.0,0.05)],
                                                 ["g_multiplier", "Green", "float_slider", (0.05,1.0,0.05)],
                                                 ["b_multiplier", "Blue", "float_slider", (0.05,1.0,0.05)]],
                                        "Power":[["color_mode", "Color Mode", "dropdown", config.settings["gradients"]],
                                                 ["s_color", "Spark Color ", "dropdown", config.settings["colors"]],
                                                 ["s_count", "Spark Amount", "slider", (0,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//6,1)],
                                                 ["mirror", "Mirror", "checkbox"],
                                                 ["flip_lr", "Flip LR", "checkbox"]],
                                       "Single":[["color", "Color", "dropdown", config.settings["colors"]]],
                                         "Beat":[["color", "Color", "dropdown", config.settings["colors"]],
                                                 ["decay", "Flash Decay", "float_slider", (0.3,0.98,0.005)]],
                                         "Bars":[["color_mode", "Color Mode", "dropdown", config.settings["gradients"]],
                                                 ["resolution", "Resolution", "slider", (1, config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"], 1)],
                                                 ["roll_speed", "Roll Speed", "slider", (0,8,1)],
                                                 ["flip_lr", "Flip LR", "checkbox"],
                                                 ["mirror", "Mirror", "checkbox"],
                                                 ["reverse_roll", "Reverse Roll", "checkbox"]],
                                     "Gradient":[["color_mode", "Color Mode", "dropdown", config.settings["gradients"]],
                                                 ["roll_speed", "Roll Speed", "slider", (0,8,1)],
                                                 ["mirror", "Mirror", "checkbox"],
                                                 ["reverse", "Reverse", "checkbox"]],
                                         "Fade":[["color_mode", "Color Mode", "dropdown", config.settings["gradients"]],
                                                 ["roll_speed", "Fade Speed", "slider", (0,8,1)],
                                                 ["reverse", "Reverse", "checkbox"]],
                                  "Calibration":[["r", "Red value", "slider", (0,255,1)],
                                                 ["g", "Green value", "slider", (0,255,1)],
                                                 ["b", "Blue value", "slider", (0,255,1)]]
                                       }
        # Setup for latency timer
        self.latency_deque = deque(maxlen=1000)
        # Setup for "Wave" (don't change these)
        self.wave_wipe_count = 0
        # Setup for "Power" (don't change these)
        self.power_indexes = []
        self.power_brightness = 0
        # Setup for multicolour modes (don't mess with this either unless you want to add in your own multicolour modes)
        # If there's a multicolour mode you would like to see, let me know on GitHub! 

        #def _vect_easing_func_gen(slope=2.5, length=1):
        #    return np.vectorize(_easing_func)

        def _easing_func(x, length, slope=2.5):
            # returns a nice eased curve with defined length and curve
            xa = (x/length)**slope
            return xa / (xa + (1 - (x/length))**slope)


        def _easing_gradient_generator(colors, length):
            """
            returns np.array of given length that eases between specified colours

            parameters:
            colors - list, colours must be in config.settings["colors"]
                eg. ["Red", "Orange", "Blue", "Purple"]
            length - int, length of array to return. should be from config.settings
                eg. config.settings["devices"]["my strip"]["configuration"]["N_PIXELS"]
            """
            colors = colors[::-1] # needs to be reversed, makes it easier to deal with
            n_transitions = len(colors) - 1
            ease_length = length // n_transitions
            pad = length - (n_transitions * ease_length)
            output = np.zeros((3, length))
            ease = np.array([_easing_func(i, ease_length, slope=2.5) for i in range(ease_length)])
            # for r,g,b
            for i in range(3):
                # for each transition
                for j in range(n_transitions):
                    # Starting ease value
                    start_value = config.settings["colors"][colors[j]][i]
                    # Ending ease value
                    end_value = config.settings["colors"][colors[j+1]][i]
                    # Difference between start and end
                    diff = end_value - start_value
                    # Make array of all start value
                    base = np.empty(ease_length)
                    base.fill(start_value)
                    # Make array of the difference between start and end
                    diffs = np.empty(ease_length)
                    diffs.fill(diff)
                    # run diffs through easing function to make smooth curve
                    eased_diffs = diffs * ease
                    # add transition to base values to produce curve from start to end value
                    base += eased_diffs
                    # append this to the output array
                    output[i, j*ease_length:(j+1)*ease_length] = base
            # cast to int
            output = np.asarray(output, dtype=int)
            # pad out the ends (bit messy but it works and looks good)
            if pad:
                for i in range(3):
                    output[i, -pad:] = output[i, -pad-1]
            return output

        self.multicolor_modes = {}
        for gradient in config.settings["gradients"]:
            self.multicolor_modes[gradient] = _easing_gradient_generator(config.settings["gradients"][gradient],
                                                                         config.settings["devices"][self.board]["configuration"]["N_PIXELS"])

        # # chunks of colour gradients
        # _blank_overlay = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # # used to construct rgb overlay. [0-255,255...] whole length of strip
        
        # _gradient_whole = [int(i*config.settings["configuration"]["MAX_BRIGHTNESS"]/(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2))\
        #                         for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2)] +\
        #                   [config.settings["configuration"]["MAX_BRIGHTNESS"] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2)]
        # # also used to make bits and pieces. [0-255], 1/2 length of strip
        # _alt_gradient_half = [int(i*config.settings["configuration"]["MAX_BRIGHTNESS"]/(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2))\
        #                         for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2)]
        # # used to construct rgb overlay. [0-255,255...] 1/2 length of strip
        # _gradient_half = _gradient_whole[::2]
        # # Spectral colour mode
        # self.multicolor_modes["Spectral"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Spectral"][2, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2] = _gradient_half[::-1]
        # self.multicolor_modes["Spectral"][1, :] = _gradient_half + _gradient_half[::-1]
        # self.multicolor_modes["Spectral"][0, :] = np.flipud(self.multicolor_modes["Spectral"][2])
        # # Dancefloor colour mode
        # self.multicolor_modes["Dancefloor"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Dancefloor"][2, :] = _gradient_whole[::-1]
        # self.multicolor_modes["Dancefloor"][0, :] = _gradient_whole
        # # Brilliance colour mode
        # self.multicolor_modes["Brilliance"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Brilliance"][2, :] = _gradient_whole[::-1]
        # self.multicolor_modes["Brilliance"][1, :] = 255
        # self.multicolor_modes["Brilliance"][0, :] = _gradient_whole
        # # Jungle colour mode
        # self.multicolor_modes["Jungle"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Jungle"][1, :] = _gradient_whole[::-1]
        # self.multicolor_modes["Jungle"][0, :] = _gradient_whole
        # # Sky colour mode
        # self.multicolor_modes["Sky"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Sky"][1, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2] = _alt_gradient_half[::-1]
        # self.multicolor_modes["Sky"][0, config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2:] = _alt_gradient_half
        # self.multicolor_modes["Sky"][2, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]] = 255
        # # Acid colour mode
        # self.multicolor_modes["Acid"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Acid"][2, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2] = _alt_gradient_half[::-1]
        # self.multicolor_modes["Acid"][1, :] = 255
        # self.multicolor_modes["Acid"][0, config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2:] = _alt_gradient_half
        # # Ocean colour mode
        # self.multicolor_modes["Ocean"] = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        # self.multicolor_modes["Ocean"][1, :] = _gradient_whole
        # self.multicolor_modes["Ocean"][2, :] = _gradient_whole[::-1]
        for i in self.multicolor_modes:
            self.multicolor_modes[i] = np.concatenate((self.multicolor_modes[i][:, ::-1],
                                                       self.multicolor_modes[i]), axis=1)

    def get_vis(self, y, audio_input):
        self.update_freq_channels(y)
        self.detect_freqs()
        time1 = time.time()
        if config.settings["devices"][self.board]["configuration"]["current_effect"] in self.non_reactive_effects:
            self.prev_output = self.effects[config.settings["devices"][self.board]["configuration"]["current_effect"]]()
        elif audio_input:
            self.prev_output = self.effects[config.settings["devices"][self.board]["configuration"]["current_effect"]](y)
        else:
            self.prev_output = np.multiply(self.prev_output, 0.95)
        time2 = time.time()
        self.latency_deque.append(1000*(time2-time1))
        if config.settings["configuration"]["USE_GUI"]:
            gui.label_latency.setText("{} ms Processing Latency   ".format(int(sum(self.latency_deque)/len(self.latency_deque))))
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
        for i in range(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]):
            channel_avgs.append(sum(self.freq_channels[i])/len(self.freq_channels[i]))
            differences.append(((self.freq_channels[i][0]-channel_avgs[i])*100)//channel_avgs[i])
        for i in ["beat", "low", "mid", "high"]:
            if any(differences[j] >= self.min_percent_diff[i]\
                   and self.freq_channels[j][0] >= self.min_detect_amplitude[i]\
                            for j in range(*self.detection_ranges[i]))\
                        and (time.time() - self.prev_freq_detects[i] > 0.1)\
                        and len(self.freq_channels[0]) == self.freq_channel_history:
                self.prev_freq_detects[i] = time.time()
                self.current_freq_detects[i] = True
                #print(i)
            else:
                self.current_freq_detects[i] = False                

    def visualize_scroll(self, y):
        """Effect that originates in the center and scrolls outwards"""
        global p
        y = y**4.0
        signal_processers[self.board].gain.update(y)
        y /= signal_processers[self.board].gain.value
        y *= 255.0
        r = int(np.max(y[:len(y) // 3])*config.settings["devices"][self.board]["effect_opts"]["Scroll"]["r_multiplier"])
        g = int(np.max(y[len(y) // 3: 2 * len(y) // 3])*config.settings["devices"][self.board]["effect_opts"]["Scroll"]["g_multiplier"])
        b = int(np.max(y[2 * len(y) // 3:])*config.settings["devices"][self.board]["effect_opts"]["Scroll"]["b_multiplier"])
        # Scrolling effect window
        speed = config.settings["devices"][self.board]["effect_opts"]["Scroll"]["speed"]
        p[:, speed:] = p[:, :-speed]
        p *= config.settings["devices"][self.board]["effect_opts"]["Scroll"]["decay"]
        p = gaussian_filter1d(p, sigma=config.settings["devices"][self.board]["effect_opts"]["Scroll"]["blur"])
        # Create new color originating at the center
        p[0, :speed] = r
        p[1, :speed] = g
        p[2, :speed] = b
        # Update the LED strip
        return np.concatenate((p[:, ::-1], p), axis=1)

    def visualize_energy(self, y):
        """Effect that expands from the center with increasing sound energy"""
        global p
        y = np.copy(y)
        signal_processers[self.board].gain.update(y)
        y /= signal_processers[self.board].gain.value
        scale = config.settings["devices"][self.board]["effect_opts"]["Energy"]["scale"]
        # Scale by the width of the LED strip
        y *= float((config.settings["devices"][self.board]["configuration"]["N_PIXELS"] * scale) - 1)
        # Map color channels according to energy in the different freq bands
        r = int(np.mean(y[:len(y) // 3]**scale)*config.settings["devices"][self.board]["effect_opts"]["Energy"]["r_multiplier"])
        g = int(np.mean(y[len(y) // 3: 2 * len(y) // 3]**scale)*config.settings["devices"][self.board]["effect_opts"]["Energy"]["g_multiplier"])
        b = int(np.mean(y[2 * len(y) // 3:]**scale)*config.settings["devices"][self.board]["effect_opts"]["Energy"]["b_multiplier"])
        # Assign color to different frequency regions
        p[0, :r] = 255.0
        p[0, r:] = 0.0
        p[1, :g] = 255.0
        p[1, g:] = 0.0
        p[2, :b] = 255.0
        p[2, b:] = 0.0
        signal_processers[self.board].p_filt.update(p)
        p = np.round(signal_processers[self.board].p_filt.value)
        # Apply blur to smooth the edges
        p[0, :] = gaussian_filter1d(p[0, :], sigma=config.settings["devices"][self.board]["effect_opts"]["Energy"]["blur"])
        p[1, :] = gaussian_filter1d(p[1, :], sigma=config.settings["devices"][self.board]["effect_opts"]["Energy"]["blur"])
        p[2, :] = gaussian_filter1d(p[2, :], sigma=config.settings["devices"][self.board]["effect_opts"]["Energy"]["blur"])
        # Set the new pixel value
        return np.concatenate((p[:, ::-1], p), axis=1)

    def visualize_wavelength(self, y):
        y = np.copy(interpolate(y, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2))
        signal_processers[self.board].common_mode.update(y)
        diff = y - self.prev_spectrum
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = signal_processers[self.board].r_filt.update(y - signal_processers[self.board].common_mode.value)
        #g = np.abs(diff)
        b = signal_processers[self.board].b_filt.update(np.copy(y))
        r = np.array([j for i in zip(r,r) for j in i])
        output = np.array([self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["color_mode"]][0][
                                    (config.settings["devices"][self.board]["configuration"]["N_PIXELS"] if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_grad"] else 0):
                                    (None if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_grad"] else config.settings["devices"][self.board]["configuration"]["N_PIXELS"]):]*r,
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["color_mode"]][1][
                                    (config.settings["devices"][self.board]["configuration"]["N_PIXELS"] if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_grad"] else 0):
                                    (None if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_grad"] else config.settings["devices"][self.board]["configuration"]["N_PIXELS"]):]*r,
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["color_mode"]][2][
                                    (config.settings["devices"][self.board]["configuration"]["N_PIXELS"] if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_grad"] else 0):
                                    (None if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_grad"] else config.settings["devices"][self.board]["configuration"]["N_PIXELS"]):]*r])
        #self.prev_spectrum = y
        self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["color_mode"]] = np.roll(
                    self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["color_mode"]],
                    config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["roll_speed"]*(-1 if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["reverse_roll"] else 1),
                    axis=1)
        output[0] = gaussian_filter1d(output[0], sigma=config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["blur"])
        output[1] = gaussian_filter1d(output[1], sigma=config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["blur"])
        output[2] = gaussian_filter1d(output[2], sigma=config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["blur"])
        if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["flip_lr"]:
            output = np.fliplr(output)
        if config.settings["devices"][self.board]["effect_opts"]["Wavelength"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output
    
    def visualize_spectrum(self, y):
        """Effect that maps the Mel filterbank frequencies onto the LED strip"""
        global p
        #print(len(y))
        #print(y)
        y = np.copy(interpolate(y, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2))
        signal_processers[self.board].common_mode.update(y)
        diff = y - self.prev_spectrum
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = signal_processers[self.board].r_filt.update(y - signal_processers[self.board].common_mode.value)
        g = np.abs(diff)
        b = signal_processers[self.board].b_filt.update(np.copy(y))
        r *= config.settings["devices"][self.board]["effect_opts"]["Spectrum"]["r_multiplier"]
        g *= config.settings["devices"][self.board]["effect_opts"]["Spectrum"]["g_multiplier"]
        b *= config.settings["devices"][self.board]["effect_opts"]["Spectrum"]["b_multiplier"]
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
            output = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
            output[0][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_flash"]][0]
            output[1][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_flash"]][1]
            output[2][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_flash"]][2]
            self.wave_wipe_count = config.settings["devices"][self.board]["effect_opts"]["Wave"]["wipe_len"]
        else:
            output = np.copy(self.prev_output)
            #for i in range(len(self.prev_output)):
            #    output[i] = np.hsplit(self.prev_output[i],2)[0]
            output = np.multiply(self.prev_output,config.settings["devices"][self.board]["effect_opts"]["Wave"]["decay"])
            for i in range(self.wave_wipe_count):
                output[0][i]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_wave"]][0]
                output[0][-i]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_wave"]][0]
                output[1][i]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_wave"]][1]
                output[1][-i]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_wave"]][1]
                output[2][i]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_wave"]][2]
                output[2][-i]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Wave"]["color_wave"]][2]
            #output = np.concatenate([output,np.fliplr(output)], axis=1)
            if self.wave_wipe_count > config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2:
                self.wave_wipe_count = config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//2
            self.wave_wipe_count += config.settings["devices"][self.board]["effect_opts"]["Wave"]["wipe_speed"]
        return output

    def visualize_beat(self, y):
        """Effect that flashes to the beat"""
        if self.current_freq_detects["beat"]:
            output = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
            output[0][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Beat"]["color"]][0]
            output[1][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Beat"]["color"]][1]
            output[2][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Beat"]["color"]][2]
        else:
            output = np.copy(self.prev_output)
            output = np.multiply(self.prev_output,config.settings["devices"][self.board]["effect_opts"]["Beat"]["decay"])
        return output

    def visualize_bars(self, y):
        # Bit of fiddling with the y values
        y = np.copy(interpolate(y, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2))
        signal_processers[self.board].common_mode.update(y)
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = signal_processers[self.board].r_filt.update(y - signal_processers[self.board].common_mode.value)
        r = np.array([j for i in zip(r,r) for j in i])
        # Split y into [resulution] chunks and calculate the average of each
        max_values = np.array([max(i) for i in np.array_split(r, config.settings["devices"][self.board]["effect_opts"]["Bars"]["resolution"])])
        max_values = np.clip(max_values, 0, 1)
        color_sets = []
        for i in range(config.settings["devices"][self.board]["effect_opts"]["Bars"]["resolution"]):
            # [r,g,b] values from a multicolour gradient array at [resulution] equally spaced intervals
            color_sets.append([self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Bars"]["color_mode"]]\
                              [j][i*(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//config.settings["devices"][self.board]["effect_opts"]["Bars"]["resolution"])] for j in range(3)])
        output = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        chunks = np.array_split(output[0], config.settings["devices"][self.board]["effect_opts"]["Bars"]["resolution"])
        n = 0
        # Assign blocks with heights corresponding to max_values and colours from color_sets
        for i in range(len(chunks)):
            m = len(chunks[i])
            for j in range(3):
                output[j][n:n+m] = color_sets[i][j]*max_values[i]
            n += m
        self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Bars"]["color_mode"]] = np.roll(
                    self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Bars"]["color_mode"]],
                    config.settings["devices"][self.board]["effect_opts"]["Bars"]["roll_speed"]*(-1 if config.settings["devices"][self.board]["effect_opts"]["Bars"]["reverse_roll"] else 1),
                    axis=1)
        if config.settings["devices"][self.board]["effect_opts"]["Bars"]["flip_lr"]:
            output = np.fliplr(output)
        if config.settings["devices"][self.board]["effect_opts"]["Bars"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output

    def visualize_power(self, y):
        #config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]
        # Bit of fiddling with the y values
        y = np.copy(interpolate(y, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2))
        signal_processers[self.board].common_mode.update(y)
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = signal_processers[self.board].r_filt.update(y - signal_processers[self.board].common_mode.value)
        r = np.array([j for i in zip(r,r) for j in i])
        output = np.array([self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]][0, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]]*r,
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]][1, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]]*r,
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]][2, :config.settings["devices"][self.board]["configuration"]["N_PIXELS"]]*r])
        # if there's a high (eg clap):
        if self.current_freq_detects["high"]:
            self.power_brightness = 1.0
            # Generate random indexes
            self.power_indexes = random.sample(range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"]), config.settings["devices"][self.board]["effect_opts"]["Power"]["s_count"])
            #print("ye")
        # Assign colour to the random indexes
        for index in self.power_indexes:
            output[0, index] = int(config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Power"]["s_color"]][0]*self.power_brightness)
            output[1, index] = int(config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Power"]["s_color"]][1]*self.power_brightness)
            output[2, index] = int(config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Power"]["s_color"]][2]*self.power_brightness)
        # Remove some of the indexes for next time
        self.power_indexes = [i for i in self.power_indexes if i not in random.sample(self.power_indexes, len(self.power_indexes)//4)]
        if len(self.power_indexes) <= 4:
            self.power_indexes = []
        # Fade the colour of the sparks out a bit for next time
        if self.power_brightness > 0:
            self.power_brightness -= 0.05
        # Calculate length of bass bar based on max bass frequency volume and length of strip
        strip_len = int((config.settings["devices"][self.board]["configuration"]["N_PIXELS"]//3)*max(y[:int(config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]*0.2)]))
        # Add the bass bars into the output. Colour proportional to length
        output[0][:strip_len] = self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]][0][strip_len]
        output[1][:strip_len] = self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]][1][strip_len]
        output[2][:strip_len] = self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Power"]["color_mode"]][2][strip_len]
        if config.settings["devices"][self.board]["effect_opts"]["Power"]["flip_lr"]:
            output = np.fliplr(output)
        if config.settings["devices"][self.board]["effect_opts"]["Power"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output

    def visualize_pulse(self, y):
        """fckin dope ass visuals that's what"""
        config.settings["devices"][self.board]["effect_opts"]["Pulse"]["bar_color"]
        config.settings["devices"][self.board]["effect_opts"]["Pulse"]["bar_speed"]
        config.settings["devices"][self.board]["effect_opts"]["Pulse"]["bar_length"]
        config.settings["devices"][self.board]["effect_opts"]["Pulse"]["color_mode"]
        y = np.copy(interpolate(y, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2))
        common_mode.update(y) # i honestly have no idea what this is but i just work with it rather than trying to figure it out
        self.prev_spectrum = np.copy(y)
        # Color channel mappings
        r = r_filt.update(y - common_mode.value) # same with this, no flippin clue
        r = np.array([j for i in zip(r,r) for j in i])
        output = np.array([self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Pulse"]["color_mode"]][0][:config.settings["devices"][self.board]["configuration"]["N_PIXELS"]],
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Pulse"]["color_mode"]][1][:config.settings["devices"][self.board]["configuration"]["N_PIXELS"]],
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Pulse"]["color_mode"]][2][:config.settings["devices"][self.board]["configuration"]["N_PIXELS"]]])
        
    def visualize_single(self):
        "Displays a single colour, non audio reactive"
        output = np.zeros((3,config.settings["devices"][self.board]["configuration"]["N_PIXELS"]))
        output[0][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Single"]["color"]][0]
        output[1][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Single"]["color"]][1]
        output[2][:]=config.settings["colors"][config.settings["devices"][self.board]["effect_opts"]["Single"]["color"]][2]
        return output

    def visualize_gradient(self):
        "Displays a multicolour gradient, non audio reactive"
        output = np.array([self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Gradient"]["color_mode"]][0][:config.settings["devices"][self.board]["configuration"]["N_PIXELS"]],
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Gradient"]["color_mode"]][1][:config.settings["devices"][self.board]["configuration"]["N_PIXELS"]],
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Gradient"]["color_mode"]][2][:config.settings["devices"][self.board]["configuration"]["N_PIXELS"]]])
        self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Gradient"]["color_mode"]] = np.roll(
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Gradient"]["color_mode"]],
                           config.settings["devices"][self.board]["effect_opts"]["Gradient"]["roll_speed"]*(-1 if config.settings["devices"][self.board]["effect_opts"]["Gradient"]["reverse"] else 1),
                           axis=1)
        if config.settings["devices"][self.board]["effect_opts"]["Gradient"]["mirror"]:
            output = np.concatenate((output[:, ::-2], output[:, ::2]), axis=1)
        return output

    def visualize_fade(self):
        "Fades through a multicolour gradient, non audio reactive"
        output = np.array([[self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Fade"]["color_mode"]][0][0] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])],
                           [self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Fade"]["color_mode"]][1][0] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])],
                           [self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Fade"]["color_mode"]][2][0] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])]])
        self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Fade"]["color_mode"]] = np.roll(
                           self.multicolor_modes[config.settings["devices"][self.board]["effect_opts"]["Fade"]["color_mode"]],
                           config.settings["devices"][self.board]["effect_opts"]["Fade"]["roll_speed"]*(-1 if config.settings["devices"][self.board]["effect_opts"]["Fade"]["reverse"] else 1),
                           axis=1)
        return output

    def visualize_calibration(self):
        "Custom values for RGB"
        output = np.array([[config.settings["devices"][self.board]["effect_opts"]["Calibration"]["r"] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])],
                           [config.settings["devices"][self.board]["effect_opts"]["Calibration"]["g"] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])],
                           [config.settings["devices"][self.board]["effect_opts"]["Calibration"]["b"] for i in range(config.settings["devices"][self.board]["configuration"]["N_PIXELS"])]])
        return output
       
class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initMainWindow()
        self.updateUIVisibleItems()

    def initMainWindow(self):
        # ==================================== Set up window and wrapping layout
        self.setWindowTitle("Visualization")
        # Initial window size/pos last saved if available
        settings.beginGroup("MainWindow")
        if not settings.value("geometry") == None:
            self.restoreGeometry(settings.value("geometry"))
        if not settings.value("state") == None:
            self.restoreState(settings.value("state"))
        settings.endGroup()
        self.main_wrapper = QVBoxLayout()

        # ======================================================= Set up toolbar
        #toolbar_guiDialogue.setShortcut('Ctrl+H')
        toolbar_guiDialogue = QAction('GUI Properties', self)
        toolbar_guiDialogue.triggered.connect(self.guiDialogue)
        #toolbar_configDialogue = QAction('GUI Properties', self)
        #toolbar_configDialogue.triggered.connect(self.configDialogue)
        
        self.toolbar = self.addToolBar('top_toolbar')
        self.toolbar.setObjectName('top_toolbar')
        self.toolbar.addAction(toolbar_guiDialogue)
       # self.toolbar.addAction(toolbar_configDialogue)

        # ========================================== Set up FPS and error labels
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.label_error = QLabel("")
        self.label_fps = QLabel("")
        self.label_latency = QLabel("")
        self.label_fps.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label_latency.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.statusbar.addPermanentWidget(self.label_error, stretch=1)
        self.statusbar.addPermanentWidget(self.label_latency)
        self.statusbar.addPermanentWidget(self.label_fps)

        # ==================================================== Set up board tabs
        self.label_boards = QLabel("Boards")
        self.boardsTabWidget = QTabWidget()
        # Dynamically set up boards tabs
        self.board_tabs = {}         # contains all the tabs for each board
        self.board_tabs_widgets = {} # contains all the widgets for each tab
        for board in config.settings["devices"]:
            # Make the tab
            self.addBoard(board)
        self.main_wrapper.addWidget(self.label_boards)
        self.main_wrapper.addWidget(self.boardsTabWidget)
        self.setLayout(self.main_wrapper)

        # =========================================== Set wrapper as main widget
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.main_wrapper)
        self.show()

    def addBoard(self, board):
        self.board_tabs_widgets[board] = {}
        self.board_tabs[board] = QWidget()

        self.initBoardUI(board)
        self.boardsTabWidget.addTab(self.board_tabs[board],board)
        self.board_tabs[board].setLayout(self.board_tabs_widgets[board]["wrapper"])
        pass

    def closeEvent(self, event):
        # executed when the window is being closed
        quit_msg = "Are you sure you want to exit?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Save window state
            settings.beginGroup("MainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue('state', self.saveState())
            settings.endGroup()
            # save all settings
            settings.setValue("settings_dict", config.settings)
            # save and close
            settings.sync()
            event.accept()
            sys.exit(0)
            
        else:
            event.ignore()

    def updateUIVisibleItems(self):
        for section in self.gui_widgets:
            for widget in self.gui_widgets[section]:
                widget.setVisible(config.settings["GUI_opts"][section])

    def guiDialogue(self):
        def update_visibilty_dict():
            for checkbox in self.gui_vis_checkboxes:
                config.settings["GUI_opts"][checkbox] = self.gui_vis_checkboxes[checkbox].isChecked()
            self.updateUIVisibleItems()

        self.gui_dialogue = QDialog(None, Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.gui_dialogue.setWindowTitle("GUI Properties")
        self.gui_dialogue.setWindowModality(Qt.ApplicationModal)
        layout = QGridLayout()
        self.gui_dialogue.setLayout(layout)
        # OK button
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.gui_dialogue.accept)

        self.gui_vis_checkboxes = {}
        for section in self.gui_widgets:
            self.gui_vis_checkboxes[section] = QCheckBox(section)
            self.gui_vis_checkboxes[section].setCheckState(
                    Qt.Checked if config.settings["GUI_opts"][section] else Qt.Unchecked)
            self.gui_vis_checkboxes[section].stateChanged.connect(update_visibilty_dict)
            layout.addWidget(self.gui_vis_checkboxes[section])
        layout.addWidget(self.buttons)
        self.gui_dialogue.show()

    def configDialogue(self):
        def update_visibilty_dict():
            for checkbox in self.gui_vis_checkboxes:
                config.settings["GUI_opts"][checkbox] = self.gui_vis_checkboxes[checkbox].isChecked()
            self.updateUIVisibleItems()

        self.gui_dialogue = QDialog(None, Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.gui_dialogue.setWindowTitle("GUI Properties")
        self.gui_dialogue.setWindowModality(Qt.ApplicationModal)
        layout = QGridLayout()
        self.gui_dialogue.setLayout(layout)
        # OK button
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.gui_dialogue.accept)

        self.gui_vis_checkboxes = {}
        for section in self.gui_widgets:
            self.gui_vis_checkboxes[section] = QCheckBox(section)
            self.gui_vis_checkboxes[section].setCheckState(
                    Qt.Checked if config.settings["GUI_opts"][section] else Qt.Unchecked)
            self.gui_vis_checkboxes[section].stateChanged.connect(update_visibilty_dict)
            layout.addWidget(self.gui_vis_checkboxes[section])
        layout.addWidget(self.buttons)
        self.gui_dialogue.show()
        
    def initBoardUI(self, board):
        self.board = board
        # =============================================== Set up wrapping layout
        self.board_tabs_widgets[board]["wrapper"] = QVBoxLayout()
        
        # ================================================== Set up graph layout
        self.board_tabs_widgets[board]["graph_view"] = pg.GraphicsView()
        graph_layout = pg.GraphicsLayout(border=(100,100,100))
        self.board_tabs_widgets[board]["graph_view"].setCentralItem(graph_layout)
        # Mel filterbank plot
        fft_plot = graph_layout.addPlot(title='Filterbank Output', colspan=3)
        fft_plot.setRange(yRange=[-0.1, 1.2])
        fft_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        x_data = np.array(range(1, config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"] + 1))
        self.board_tabs_widgets[board]["mel_curve"] = pg.PlotCurveItem()
        self.board_tabs_widgets[board]["mel_curve"].setData(x=x_data, y=x_data*0)
        fft_plot.addItem(self.board_tabs_widgets[board]["mel_curve"])
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
        self.board_tabs_widgets[board]["r_curve"] = pg.PlotCurveItem(pen=r_pen)
        self.board_tabs_widgets[board]["g_curve"] = pg.PlotCurveItem(pen=g_pen)
        self.board_tabs_widgets[board]["b_curve"] = pg.PlotCurveItem(pen=b_pen)
        # Define x data
        x_data = np.array(range(1, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] + 1))
        self.board_tabs_widgets[board]["r_curve"].setData(x=x_data, y=x_data*0)
        self.board_tabs_widgets[board]["g_curve"].setData(x=x_data, y=x_data*0)
        self.board_tabs_widgets[board]["b_curve"].setData(x=x_data, y=x_data*0)
        # Add curves to plot
        led_plot.addItem(self.board_tabs_widgets[board]["r_curve"])
        led_plot.addItem(self.board_tabs_widgets[board]["g_curve"])
        led_plot.addItem(self.board_tabs_widgets[board]["b_curve"])

        # ================================================= Set up button layout
        self.board_tabs_widgets[board]["label_reactive"] = QLabel("Audio Reactive Effects")
        self.board_tabs_widgets[board]["label_non_reactive"] = QLabel("Non Reactive Effects")
        self.board_tabs_widgets[board]["reactive_button_grid_wrap"] = QWidget()
        self.board_tabs_widgets[board]["non_reactive_button_grid_wrap"] = QWidget()
        self.board_tabs_widgets[board]["reactive_button_grid"] = QGridLayout()
        self.board_tabs_widgets[board]["non_reactive_button_grid"] = QGridLayout()
        self.board_tabs_widgets[board]["reactive_button_grid_wrap"].setLayout(self.board_tabs_widgets[board]["reactive_button_grid"])   
        self.board_tabs_widgets[board]["non_reactive_button_grid_wrap"].setLayout(self.board_tabs_widgets[board]["non_reactive_button_grid"])   
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
                config.settings["devices"][board]["configuration"]["current_effect"] = effect
                buttons[effect].setDown(True)
            func.__name__ = effect
            return func
        # Where the magic happens
        for effect in visualizers[board].effects:
            if not effect in visualizers[board].non_reactive_effects:
                connecting_funcs[effect] = connect_generator(effect)
                buttons[effect] = QPushButton(effect)
                buttons[effect].clicked.connect(connecting_funcs[effect])
                self.board_tabs_widgets[board]["reactive_button_grid"].addWidget(buttons[effect], j, i)
                i += 1
                if i % grid_width == 0:
                    i = 0
                    j += 1
            else:
                connecting_funcs[effect] = connect_generator(effect)
                buttons[effect] = QPushButton(effect)
                buttons[effect].clicked.connect(connecting_funcs[effect])
                self.board_tabs_widgets[board]["non_reactive_button_grid"].addWidget(buttons[effect], l, k)
                k += 1
                if k % grid_width == 0:
                    k = 0
                    l += 1
                
        # ============================================== Set up frequency slider
        # Frequency range label
        self.board_tabs_widgets[board]["label_slider"] = QLabel("Frequency Range")
        # Frequency slider
        def freq_slider_change(tick):
            minf = self.board_tabs_widgets[board]["freq_slider"].tickValue(0)**2.0 * (config.settings["configuration"]["MIC_RATE"] / 2.0)
            maxf = self.board_tabs_widgets[board]["freq_slider"].tickValue(1)**2.0 * (config.settings["configuration"]["MIC_RATE"] / 2.0)
            t = 'Frequency range: {:.0f} - {:.0f} Hz'.format(minf, maxf)
            freq_label.setText(t)
            config.settings["configuration"]["MIN_FREQUENCY"] = minf
            config.settings["configuration"]["MAX_FREQUENCY"] = maxf
            dsp.create_mel_bank()
        def set_freq_min():
            config.settings["configuration"]["MIN_FREQUENCY"] = self.board_tabs_widgets[board]["freq_slider"].start()
            dsp.create_mel_bank()
        def set_freq_max():
            config.settings["configuration"]["MAX_FREQUENCY"] = self.board_tabs_widgets[board]["freq_slider"].end()
            dsp.create_mel_bank()
        self.board_tabs_widgets[board]["freq_slider"] = QRangeSlider()
        self.board_tabs_widgets[board]["freq_slider"].show()
        self.board_tabs_widgets[board]["freq_slider"].setMin(0)
        self.board_tabs_widgets[board]["freq_slider"].setMax(20000)
        self.board_tabs_widgets[board]["freq_slider"].setRange(config.settings["configuration"]["MIN_FREQUENCY"], config.settings["configuration"]["MAX_FREQUENCY"])
        self.board_tabs_widgets[board]["freq_slider"].setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        self.board_tabs_widgets[board]["freq_slider"].setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')
        self.board_tabs_widgets[board]["freq_slider"].setDrawValues(True)
        self.board_tabs_widgets[board]["freq_slider"].endValueChanged.connect(set_freq_max)
        self.board_tabs_widgets[board]["freq_slider"].startValueChanged.connect(set_freq_min)
        self.board_tabs_widgets[board]["freq_slider"].setStyleSheet("""
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
        self.board_tabs_widgets[board]["label_options"] = QLabel("Effect Options")
        self.board_tabs_widgets[board]["opts_tabs"] = QTabWidget()
        # Dynamically set up tabs
        tabs = {}
        grid_layouts = {}
        self.board_tabs_widgets[board]["grid_layout_widgets"] = {}
        options = config.settings["devices"][board]["effect_opts"].keys()
        for effect in visualizers[self.board].effects:
            # Make the tab
            self.board_tabs_widgets[board]["grid_layout_widgets"][effect] = {}
            tabs[effect] = QWidget()
            grid_layouts[effect] = QGridLayout()
            tabs[effect].setLayout(grid_layouts[effect])
            self.board_tabs_widgets[board]["opts_tabs"].addTab(tabs[effect],effect)
            # These functions make functions for the dynamic ui generation
            # YOU WANT-A DYNAMIC I GIVE-A YOU DYNAMIC!
            def gen_slider_valuechanger(effect, key):
                def func():
                    config.settings["devices"][board]["effect_opts"][effect][key] = self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].value()
                return func
            def gen_float_slider_valuechanger(effect, key):
                def func():
                    config.settings["devices"][board]["effect_opts"][effect][key] = self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].slider_value
                return func
            def gen_combobox_valuechanger(effect, key):
                def func():
                    config.settings["devices"][board]["effect_opts"][effect][key] = self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].currentText()
                return func
            def gen_checkbox_valuechanger(effect, key):
                def func():
                    config.settings["devices"][board]["effect_opts"][effect][key] = self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].isChecked()
                return func
            # Dynamically generate ui for settings
            if effect in visualizers[self.board].dynamic_effects_config:
                i = 0
                connecting_funcs[effect] = {}
                for key, label, ui_element, *opts in visualizers[self.board].dynamic_effects_config[effect]:
                    if opts: # neatest way  ^^^^^ i could think of to unpack and handle an unknown number of opts (if any) NOTE only works with py >=3.6
                        opts = list(opts[0])
                    if ui_element == "slider":
                        connecting_funcs[effect][key] = gen_slider_valuechanger(effect, key)
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key] = QSlider(Qt.Horizontal)
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].setMinimum(opts[0])
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].setMaximum(opts[1])
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].setValue(config.settings["devices"][board]["effect_opts"][effect][key])
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].valueChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "float_slider":
                        connecting_funcs[effect][key] = gen_float_slider_valuechanger(effect, key)
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key] = QFloatSlider(*opts, config.settings["devices"][board]["effect_opts"][effect][key])
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].setValue(config.settings["devices"][board]["effect_opts"][effect][key])
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].valueChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "dropdown":
                        connecting_funcs[effect][key] = gen_combobox_valuechanger(effect, key)
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key] = QComboBox()
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].addItems(opts)
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].setCurrentIndex(opts.index(config.settings["devices"][board]["effect_opts"][effect][key]))
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].currentIndexChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "checkbox":
                        connecting_funcs[effect][key] = gen_checkbox_valuechanger(effect, key)
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key] = QCheckBox()
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].stateChanged.connect(
                                connecting_funcs[effect][key])
                        self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key].setCheckState(
                                Qt.Checked if config.settings["devices"][board]["effect_opts"][effect][key] else Qt.Unchecked)
                    grid_layouts[effect].addWidget(QLabel(label),i,0)
                    grid_layouts[effect].addWidget(self.board_tabs_widgets[board]["grid_layout_widgets"][effect][key],i,1)
                    i += 1    
            else:
                grid_layouts[effect].addWidget(QLabel("No customisable options for this effect :("),0,0)
                
        
        
        # ============================================= Add layouts into self.board_tabs_widgets[board]["wrapper"]
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["graph_view"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["label_reactive"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["reactive_button_grid_wrap"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["label_non_reactive"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["non_reactive_button_grid_wrap"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["label_slider"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["freq_slider"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["label_options"])
        self.board_tabs_widgets[board]["wrapper"].addWidget(self.board_tabs_widgets[board]["opts_tabs"])
        self.gui_widgets = {"Graphs":                      [self.board_tabs_widgets[board]["graph_view"]],
                            "Reactive Effect Buttons":     [self.board_tabs_widgets[board]["label_reactive"], self.board_tabs_widgets[board]["reactive_button_grid_wrap"]],
                            "Non Reactive Effect Buttons": [self.board_tabs_widgets[board]["label_non_reactive"], self.board_tabs_widgets[board]["non_reactive_button_grid_wrap"]],
                            "Frequency Range":             [self.board_tabs_widgets[board]["label_slider"], self.board_tabs_widgets[board]["freq_slider"]],
                            "Effect Options":              [self.board_tabs_widgets[board]["label_options"], self.board_tabs_widgets[board]["opts_tabs"]]} 

class DSP():
    def __init__(self, board):
        # Name of board for which this dsp instance is processing audio
        self.board = board

        # Initialise filters etc. I've no idea what most of these are for but i imagine i'll be removing them eventually. 
        self.fft_plot_filter = dsp.ExpFilter(np.tile(1e-1, config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]), alpha_decay=0.5, alpha_rise=0.99)
        self.mel_gain =        dsp.ExpFilter(np.tile(1e-1, config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]), alpha_decay=0.01, alpha_rise=0.99)
        self.mel_smoothing =   dsp.ExpFilter(np.tile(1e-1, config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]), alpha_decay=0.5, alpha_rise=0.99)
        self.gain =            dsp.ExpFilter(np.tile(0.01, config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"]), alpha_decay=0.001, alpha_rise=0.99)
        self.r_filt =          dsp.ExpFilter(np.tile(0.01, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2), alpha_decay=0.2, alpha_rise=0.99)
        self.g_filt =          dsp.ExpFilter(np.tile(0.01, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2), alpha_decay=0.05, alpha_rise=0.3)
        self.b_filt =          dsp.ExpFilter(np.tile(0.01, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2), alpha_decay=0.1, alpha_rise=0.5)
        self.common_mode =     dsp.ExpFilter(np.tile(0.01, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2), alpha_decay=0.99, alpha_rise=0.01)
        self.p_filt =          dsp.ExpFilter(np.tile(1, (3, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2)), alpha_decay=0.1, alpha_rise=0.99)
        self.volume =          dsp.ExpFilter(config.settings["configuration"]["MIN_VOLUME_THRESHOLD"], alpha_decay=0.02, alpha_rise=0.02)
        self.p =               np.tile(1.0, (3, config.settings["devices"][self.board]["configuration"]["N_PIXELS"] // 2))
        # Number of audio samples to read every time frame
        self.samples_per_frame = int(config.settings["configuration"]["MIC_RATE"] / config.settings["configuration"]["FPS"])
        # Array containing the rolling audio sample window
        self.y_roll = np.random.rand(config.settings["configuration"]["N_ROLLING_HISTORY"], self.samples_per_frame) / 1e16
        self.fft_window =      np.hamming(int(config.settings["configuration"]["MIC_RATE"] / config.settings["configuration"]["FPS"])\
                                         * config.settings["configuration"]["N_ROLLING_HISTORY"])

        self.samples = None
        self.mel_y = None
        self.mel_x = None
        self.create_mel_bank()

    def update(self, audio_samples):
        """ Return processed audio data

        Returns mel curve, x/y data

        This is called every time there is a microphone update

        Returns
        -------
        audio_data : dict
            Dict containinng "mel", "x", and "y"
        """

        audio_data = {}
        # Normalize samples between 0 and 1
        y = audio_samples / 2.0**15
        # Construct a rolling window of audio samples
        self.y_roll[:-1] = self.y_roll[1:]
        self.y_roll[-1, :] = np.copy(y)
        y_data = np.concatenate(self.y_roll, axis=0).astype(np.float32)
        vol = np.max(np.abs(y_data))
        # Transform audio input into the frequency domain
        N = len(y_data)
        N_zeros = 2**int(np.ceil(np.log2(N))) - N
        # Pad with zeros until the next power of two
        y_data *= self.fft_window
        y_padded = np.pad(y_data, (0, N_zeros), mode='constant')
        YS = np.abs(np.fft.rfft(y_padded)[:N // 2])
        # Construct a Mel filterbank from the FFT data
        mel = np.atleast_2d(YS).T * self.mel_y.T
        # Scale data to values more suitable for visualization
        mel = np.sum(mel, axis=0)
        mel = mel**2.0
        # Gain normalization
        self.mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
        mel /= self.mel_gain.value
        mel = self.mel_smoothing.update(mel)
        x = np.linspace(config.settings["configuration"]["MIN_FREQUENCY"], config.settings["configuration"]["MAX_FREQUENCY"], len(mel))
        y = self.fft_plot_filter.update(mel)

        audio_data["mel"] = mel
        audio_data["vol"] = vol
        audio_data["x"]   = x
        audio_data["y"]   = y
        return audio_data

    def rfft(self, data, window=None):
        window = 1.0 if window is None else window(len(data))
        ys = np.abs(np.fft.rfft(data * window))
        xs = np.fft.rfftfreq(len(data), 1.0 / config.settings["configuration"]["MIC_RATE"])
        return xs, ys


    def fft(self, data, window=None):
        window = 1.0 if window is None else window(len(data))
        ys = np.fft.fft(data * window)
        xs = np.fft.fftfreq(len(data), 1.0 / config.settings["configuration"]["MIC_RATE"])
        return xs, ys


    def create_mel_bank(self):
        samples = int(config.settings["configuration"]["MIC_RATE"] * config.settings["configuration"]["N_ROLLING_HISTORY"]\
                                                   / (2.0 * config.settings["configuration"]["FPS"]))
        self.mel_y, (_, self.mel_x) = melbank.compute_melmat(num_mel_bands=config.settings["devices"][self.board]["configuration"]["N_FFT_BINS"],
                                                   freq_min=config.settings["configuration"]["MIN_FREQUENCY"],
                                                   freq_max=config.settings["configuration"]["MAX_FREQUENCY"],
                                                   num_fft_bands=samples,
                                                   sample_rate=config.settings["configuration"]["MIC_RATE"])


def update_config_dicts():
    # Updates config.settings with any values stored in settings.ini
    if settings.value("settings_dict"):
        for settings_dict in settings.value("settings_dict"):
            if not config.use_defaults[settings_dict]:
                try:
                    config.settings[settings_dict] = {**config.settings[settings_dict], **settings.value("settings_dict")[settings_dict]}
                except TypeError:
                    pass

def frames_per_second():
    """ Return the estimated frames per second

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

    # Get processed audio data for each device
    audio_datas = {}
    for board in boards:
        audio_datas[board] = signal_processers[board].update(audio_samples)
        
    outputs = {}
    
    # Visualization for each board
    for board in boards:
        # Get visualization output for each board
        audio_input = audio_datas[board]["vol"] > config.settings["configuration"]["MIN_VOLUME_THRESHOLD"]
        outputs[board] = visualizers[board].get_vis(audio_datas[board]["mel"], audio_input)
        # Map filterbank output onto LED strip(s)
        boards[board].show(outputs[board])
        if config.settings["configuration"]["USE_GUI"]:
            # Plot filterbank output
            gui.board_tabs_widgets[board]["mel_curve"].setData(x=audio_datas[board]["x"], y=audio_datas[board]["y"])
            # Plot visualizer output
            gui.board_tabs_widgets[board]["r_curve"].setData(y=outputs[board][0])
            gui.board_tabs_widgets[board]["g_curve"].setData(y=outputs[board][1])
            gui.board_tabs_widgets[board]["b_curve"].setData(y=outputs[board][2])

    # FPS update
    fps = frames_per_second()
    if time.time() - 0.5 > prev_fps_update:
        prev_fps_update = time.time()

    # Various GUI updates
    if config.settings["configuration"]["USE_GUI"]:
        # Update error label
        if audio_input:
            gui.label_error.setText("")
        else:
            gui.label_error.setText("No audio input. Volume below threshold.")
        # Update fps counter
        gui.label_fps.setText('{:.0f} / {:.0f} FPS'.format(fps, config.settings["configuration"]["FPS"]))
        app.processEvents()

    # Left in just in case prople dont use the gui
    elif vol < config.settings["configuration"]["MIN_VOLUME_THRESHOLD"]:
        print("No audio input. Volume below threshold. Volume: {}".format(vol))
    if config.settings["configuration"]["DISPLAY_FPS"]:
        print('FPS {:.0f} / {:.0f}'.format(fps, config.settings["configuration"]["FPS"]))

# Load and update configuration from settings.ini
settings = QSettings('./lib/settings.ini', QSettings.IniFormat)
settings.setFallbacksEnabled(False)    # File only, no fallback to registry
update_config_dicts()

# Initialise board(s)
visualizers = {}
boards = {}
for board in config.settings["devices"]:
    visualizers[board] = Visualizer(board)
    if config.settings["devices"][board]["configuration"]["TYPE"] == 'esp8266':
        boards[board] = devices.ESP8266(
                auto_detect=config.settings["devices"][board]["configuration"]["AUTO_DETECT"],
                   mac_addr=config.settings["devices"][board]["configuration"]["MAC_ADDR"],
                         ip=config.settings["devices"][board]["configuration"]["UDP_IP"],
                       port=config.settings["devices"][board]["configuration"]["UDP_PORT"])
    elif config.settings["devices"][board]["configuration"]["TYPE"] == 'pi':
        boards[board] = devices.RaspberryPi(
                   n_pixels=config.settings["devices"][board]["configuration"]["N_PIXELS"],
                        pin=config.settings["devices"][board]["configuration"]["LED_PIN"],
               invert_logic=config.settings["devices"][board]["configuration"]["LED_INVERT"],
                       freq=config.settings["devices"][board]["configuration"]["LED_FREQ_HZ"],
                        dma=config.settings["devices"][board]["configuration"]["LED_DMA"])
    elif config.settings["devices"][board]["configuration"]["TYPE"] == 'fadecandy':
        boards[board] = devices.FadeCandy(
                     server=config.settings["devices"][board]["configuration"]["SERVER"])
    elif config.settings["devices"][board]["configuration"]["TYPE"] == 'blinkstick':
        boards[board] = devices.BlinkStick()
    elif config.settings["devices"][board]["configuration"]["TYPE"] == 'dotstar':
        boards[board] = devices.DotStar()
    elif config.settings["devices"][board]["configuration"]["TYPE"] == 'stripless':
        pass

# Initialise DSP
signal_processers = {}
for board in config.settings["devices"]:
    signal_processers[board] = DSP(board)

# Initialise GUI 
if config.settings["configuration"]["USE_GUI"]:
    # Create GUI window
    app = QApplication([])
    app.setApplicationName('Visualization')
    gui = GUI()
    app.processEvents()

prev_fps_update = time.time()
# The previous time that the frames_per_second() function was called
_time_prev = time.time() * 1000.0
# The low-pass filter used to estimate frames-per-second
_fps = dsp.ExpFilter(val=config.settings["configuration"]["FPS"], alpha_decay=0.2, alpha_rise=0.2)

# Initialize LEDs
# led.update()
# Start listening to live audio stream
microphone.start_stream(microphone_update)
