from __future__ import print_function
from __future__ import division
import time
import numpy as np
from matplotlib import cm
import config
import features
import dsp

scroll_pixels = np.tile(0.1, config.N_PIXELS // 2)
"""Contains the pixels used in the scrolling effect"""

cmap = cm.get_cmap(config.CMAP)
"""Colormap used for applying colors to certain effects"""


def _apply_colormap(x):
    """Applies matplotlib colormap to the given np.array"""
    # x = x.clip(0, 1)
    x = np.concatenate((x, np.array([0, 0.0])))
    # Remove the padded values and only keep RGB channels
    y = 1.0 - cmap(x)[:-2, :3].T
    return y


def _downsample_peak(y, ds=2):
    """Applies downsampling using a method that preserves peak details"""
    n = len(y) // ds
    y1 = np.empty((n, 2))
    y2 = y[:n * ds].reshape((n, ds))
    y1[:, 0] = y2.max(axis=1)
    y1[:, 1] = y2.min(axis=1)
    return y1[:, 0]


def _interpolate(y, new_length):
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
    x_old = np.linspace(0, 1, len(y))
    x_new = np.linspace(0, 1, new_length)
    z = np.interp(x_new, x_old, y)
    return z


scroll_time = time.time()
scroll_origin = dsp.RealTimeExpFilter(rise=1e-2, fall=1e-2)


@dsp.ApplyExpFilter(fall=0.01, rise=1e-4, realtime=True)
def Scroll(audio_frames, pixels_per_sec=60.0):
    """Effect that originates in the center and scrolls outwards"""
    global scroll_pixels
    global scroll_time
    # Shift LED strip
    if time.time() - scroll_time > 1 / pixels_per_sec:
        scroll_time = time.time()
        scroll_pixels = np.roll(scroll_pixels, 1)
        # fall constant
        scroll_pixels *= np.exp(-2.0 / config.N_PIXELS)
        scroll_origin.value = 0.0
    # Calculate brightness of origin
    brightness = np.max(features.perceptual_spectrum(audio_frames))**4.0
    # Create new color originating at the center
    scroll_pixels[0] = np.clip(scroll_origin.update(brightness), 0, 1)
    # output = _rainbow(config.N_PIXELS, speed=1.0 / 5.0)
    pixels = np.concatenate((scroll_pixels[::-1], scroll_pixels))
    output = _apply_colormap(pixels)
    return output


@dsp.ApplyExpFilter(fall=0.01, rise=1e-4, realtime=True)
def AutoScroll(audio_frames, pixels_per_sec=60.0):
    """Effect that originates in the center and scrolls outwards"""
    global scroll_pixels
    global scroll_time
    # Shift LED strip
    if time.time() - scroll_time > 1 / pixels_per_sec:
        scroll_time = time.time()
        scroll_pixels = np.roll(scroll_pixels, 1)
        # fall constant
        scroll_pixels *= np.exp(-2.0 / config.N_PIXELS)
        scroll_origin.value = 0
    # Calculate brightness of origin
    brightness = np.max(features.auto_spectrum(audio_frames))**4.0
    # Create new color originating at the center
    scroll_pixels[0] = scroll_origin.update(brightness)
    # output = _rainbow(config.N_PIXELS, speed=1.0 / 5.0)
    pixels = np.concatenate((scroll_pixels[::-1], scroll_pixels))
    output = _apply_colormap(pixels)
    return output


# Alpha values for spectrum effect low pass exponential filter
a_rise = 1.0 - np.exp(-60.0 / (0.1 * config.N_PIXELS))
a_fall = 1.0 - np.exp(-60.0 / (1.0 * config.N_PIXELS))
lp = dsp.ExpFilter(rise=a_rise, fall=a_fall)


@dsp.ApplyExpFilter(fall=0.15, rise=0.001, realtime=True)
def Spectrum(audio_frames):
    """Effect that maps the filterbank frequencies onto the LED strip"""
    f = features.perceptual_spectrum(audio_frames)
    f = np.copy(_downsample_peak(f, len(f) // (config.N_PIXELS // 2)))
    f = np.concatenate((f[::-1], f))
    output = _apply_colormap(f)
    return output


# @dsp.ApplyExpFilter(fall=0.15, rise=0.001, realtime=True)
@dsp.ApplyExpFilter(fall=0.07, rise=0.001, realtime=True)
def Autocorrelation(audio_frames):
    """Effect that maps the filterbank frequencies onto the LED strip"""
    f = features.auto_spectrum(audio_frames)
    f = np.concatenate((f[::-1], f))
    f = f**1.15
    f = _downsample_peak(f, len(f) // (config.N_PIXELS))
    output = _apply_colormap(f)
    return output
