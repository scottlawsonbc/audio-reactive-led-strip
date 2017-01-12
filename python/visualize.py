from __future__ import print_function
from __future__ import division
import time
import numpy as np
import config
import features
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


scroll_time = time.time()


@dsp.ApplyExpFilter(fall=0.01, rise=1e-4, realtime=True)
def scroll(f, t, pixels_per_sec=60.0):
    """Effect that originates in the center and scrolls outwards"""
    global scroll_pixels
    global scroll_time
    # Shift LED strip
    if time.time() - scroll_time > 1 / pixels_per_sec:
        scroll_time = time.time()
        scroll_pixels = np.roll(scroll_pixels, 1)
        # fall constant
        scroll_pixels *= np.exp(-2.0 / config.N_PIXELS)
    # Calculate brightness of origin
    brightness = np.max(f)**4.0
    # Create new color originating at the center
    scroll_pixels[0] = brightness
    output = rainbow(config.N_PIXELS, speed=1.0 / 5.0)
    output *= np.concatenate((scroll_pixels[::-1], scroll_pixels))
    return output


rms_energy = dsp.RealTimeExpFilter(fall=3, rise=1e-3)


@dsp.ApplyExpFilter(fall=0.05, rise=0.01, realtime=True)
def energy(f, t):
    p = np.zeros((3, config.N_PIXELS // 2))
    rms = np.sqrt(np.mean(np.square(f)))
    p[:, 0] = rms / rms_energy.update(rms)
    for i in range(1, config.N_PIXELS // 2):
        p[:, i] = p[:, i - 1] * np.exp(-2.0 / config.N_PIXELS)**4
    shift = config.N_PIXELS // 4
    output = np.concatenate((p[:, ::-1], p), axis=1)
    output[1] = np.roll(output[1], shift)
    output[2] = np.roll(output[2], -shift)
    return output


# Alpha values for spectrum effect low pass exponential filter
a_rise = 1.0 - np.exp(-60.0 / (0.1 * config.N_PIXELS))
a_fall = 1.0 - np.exp(-60.0 / (4.0 * config.N_PIXELS))
lp = dsp.ExpFilter(rise=a_rise, fall=a_fall)


@dsp.ApplyExpFilter(fall=0.15, rise=0.001, realtime=True)
def spectrum(f, t, threshold=0.0):
    """Effect that maps the filterbank frequencies onto the LED strip"""
    # y = np.copy(interpolate(y**0.5, config.N_PIXELS // 2))
    f = np.copy(interpolate(f**1.5, config.N_PIXELS // 2))
    f = np.concatenate((f[::-1], f))
    f = dsp.apply_filt_lr(f, lp)
    f[f <= threshold] = 0.0
    output = rainbow(config.N_PIXELS)
    output *= f
    return output


zcr_filter = dsp.RealTimeExpFilter(rise=0.0, fall=1e-4)
"""Smooths the zero-crossing rate"""
particle_time = time.time()
particle_location = 0.0
particle_friction_mu = 0.1
particle_mass = 0.0
particle_energy = 0.0
particle_velocity = dsp.RealTimeExpFilter(rise=0.0, fall=1)


#@dsp.ApplyNormalization(rise=0.0, fall=2.0, realtime=True)
@dsp.ApplyExpFilter(fall=0.1, rise=0.0, realtime=True)
def particle(f, t, pixels_per_sec=60.0):
    global particle_time
    global particle_location
    dt = time.time() - particle_time
    particle_time += dt
    zcr = features.zero_crossing_rate(t)
    velocity = particle_velocity.update(max(0, zcr - 0.5))
    print(velocity)
    particle_location += dt * pixels_per_sec * velocity*0.2
    color = rainbow(config.N_PIXELS)
    output = np.zeros(config.N_PIXELS)
    output[int(round(particle_location)) % config.N_PIXELS] = zcr
    return output * color

    



