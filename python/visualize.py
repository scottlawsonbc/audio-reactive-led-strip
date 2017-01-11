from __future__ import print_function
from __future__ import division
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import config
import dsp

scroll_pixels = np.tile(0.1, config.N_PIXELS // 2)
"""Contains the pixels used in the scrolling effect"""


def rainbow(length, speed=1.0 / 5.0):
    """Returns a rainbow colored array with desired length

    Returns a rainbow colored array with shape (3, length).
    Each row contains the red, green, and blue color values between 0 and 1.

    Parameters
    ----------
    length : int
        The length of the rainbow colored array that should be returned

    speed : float
        Value indicating the speed that the rainbow colors change.
        If speed > 0, then successive calls to this function will return
        arrays with different colors assigned to the indices.
        If speed == 0, then this function will always return the same colors.

    Returns
    -------
    x : numpy.array
        np.ndarray with shape (3, length).
        Columns denote the red, green, and blue color values respectively.
        Each color is a float between 0 and 1.
    """
    dt = 2.0 * np.pi / length
    t = time.time() * speed
    def r(t): return (np.sin(t + 0.0) + 1.0) * 1.0 / 2.0
    def g(t): return (np.sin(t + (2.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
    def b(t): return (np.sin(t + (4.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
    x = np.tile(0.0, (length, 3))
    for i in range(length):
        x[i][0] = r(i * dt + t)
        x[i][1] = g(i * dt + t)
        x[i][2] = b(i * dt + t)
    return x.T


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
    x_old = np.linspace(0, 1, len(y))
    x_new = np.linspace(0, 1, new_length)
    z = np.interp(x_new, x_old, y)
    return z


@dsp.ApplyExpFilter(decay=0.05, rise=1e-3, realtime=True)
def scroll(y):
    """Effect that originates in the center and scrolls outwards"""
    global scroll_pixels
    # Shift LED strip
    scroll_pixels = np.roll(scroll_pixels, 1)
    scroll_pixels *= 0.98
    # Calculate brightness of origin
    brightness = np.max(y)**4.0
    # Create new color originating at the center
    scroll_pixels[0] = brightness
    scroll_pixels = gaussian_filter1d(scroll_pixels, sigma=0.1)
    output = rainbow(config.N_PIXELS, speed=1.0 / 5.0) * 255
    output *= np.concatenate((scroll_pixels[::-1], scroll_pixels))
    return output


energy_filter = dsp.ExpFilter(decay=0.2, rise=1)


@dsp.ApplyExpFilter(decay=0.5, rise=0.5, realtime=True)
def energy(y):
    """Effect that expands from the center with increasing sound energy"""
    p = np.tile(0, (3, config.N_PIXELS // 2))
    y = y * float((config.N_PIXELS // 2) - 1)
    for i in range(len(y)):
        y[i] = energy_filter.update(float(y[i]))
    # Map color channels according to energy in the different freq bands
    scale = 0.9
    r = np.round(np.mean(y[:len(y) // 3]**scale))
    g = np.round(np.mean(y[len(y) // 3: 2 * len(y) // 3]**scale))
    b = np.round(np.mean(y[2 * len(y) // 3:]**scale))
    # Assign color to different frequency regions
    p[0, :int(r)] = 255.0
    p[1, :int(g)] = 255.0
    p[2, :int(b)] = 255.0
    # Apply substantial blur to smooth the edges
    p[0, :] = gaussian_filter1d(p[0, :], sigma=3.0)
    p[1, :] = gaussian_filter1d(p[1, :], sigma=3.0)
    p[2, :] = gaussian_filter1d(p[2, :], sigma=3.0)
    # Set the new pixel value
    return np.concatenate((p[:, ::-1], p), axis=1)


@dsp.ApplyExpFilter(decay=0.05, rise=0.001, realtime=True)
def spectrum(y):
    """Effect that maps the filterbank frequencies onto the LED strip"""
    y = np.copy(interpolate(y**0.5, config.N_PIXELS // 2))
    output = rainbow(config.N_PIXELS)
    output *= np.concatenate((y[::-1], y))
    return output * 255.0
