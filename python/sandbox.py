from __future__ import print_function
from __future__ import division
import time
import numpy as np
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
import config
import microphone
import dsp
import led
import melbank
from scipy.ndimage.filters import gaussian_filter1d
from scipy.signal import argrelextrema



def rainbow(length, speed=1.0 / 5.0):
    """Returns a rainbow colored array with desired length

    Returns a rainbow colored array with shape (length, 3). 
    Each row contains the red, green, and blue color values between 0 and 1.

    Example format:
    [[red0, green0, blue0],
     [red1, green1, blue1],
            ...
     [redN, greenN, blueN]]

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
        np.ndarray with shape (length, 3).
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
    return x


def rainbow_gen(length, speed=1./5., center=0.5, width=0.5, f=[1, 1, 1]):
    dt = 2.0 * np.pi / length
    t = time.time() * speed
    phi = 2.0 / 3.0 * np.pi
    def r(t): return np.clip(np.sin(f[0] * t + 1. * phi) * width + center, 0., 1.)
    def g(t): return np.clip(np.sin(f[1] * t + 2. * phi) * width + center, 0., 1.)
    def b(t): return np.clip(np.sin(f[2] * t + 3. * phi) * width + center, 0., 1.)
    x = np.tile(0.0, (length, 3))
    for i in range(length):
        x[i][0] = r(i * dt + t)
        x[i][1] = g(i * dt + t)
        x[i][2] = b(i * dt + t)
    return x


_time_prev = time.time() * 1000.0
"""The previous time that the frames_per_second() function was called"""

_fps = dsp.ExpFilter(val=config.FPS, alpha_decay=0.05, alpha_rise=0.05)
"""The low-pass filter used to estimate frames-per-second"""


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


def update_plot_1(x, y):
    """Updates pyqtgraph plot 1

    Parameters
    ----------
    x : numpy.array
        1D array containing the X-axis values that should be plotted.
        There should only be one X-axis array.

    y : numpy.ndarray
        Array containing each of the Y-axis series that should be plotted.
        Each row of y corresponds to a Y-axis series. The columns in each row
        are the values that should be plotted.

    Returns
    -------
    None
    """
    global curves, p1
    colors = rainbow(config.N_CURVES) * 255.0
    for i in range(config.N_CURVES):
        #curves[i].setPen((colors[i][0], colors[i][1], colors[i][2]))
        curves[i].setData(x=x, y=y[i])
    p1.autoRange()
    p1.setRange(yRange=(0.0, 2.0))


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
    x_old = np.linspace(0, 1, len(y))
    x_new = np.linspace(0, 1, new_length)
    z = np.interp(x_new, x_old, y)
    return z


def leak_saturated_pixels(pixels):
    pixels = np.copy(pixels)
    for i in range(pixels.shape[0]):
        excess_red = max(pixels[i, 0] - 255.0, 0.0)
        excess_green = max(pixels[i, 1] - 255.0, 0.0)
        excess_blue = max(pixels[i, 2] - 255.0, 0.0)
        # Share excess red
        pixels[i, 1] += excess_red
        pixels[i, 2] += excess_red
        # Share excess green
        pixels[i, 0] += excess_green
        pixels[i, 2] += excess_green
        # Share excess blue
        pixels[i, 0] += excess_blue
        pixels[i, 1] += excess_blue
    return pixels


_EA_norm = dsp.ExpFilter(np.tile(1e-4, config.N_PIXELS), 0.01, 0.85)
"""Onset energy per-bin normalization constants

This filter is responsible for individually normalizing the onset bin energies.
This is used to obtain per-bin automatic gain control.
"""

_EA_smooth = dsp.ExpFilter(np.tile(1.0, config.N_PIXELS), 0.25, 0.80)
"""Asymmetric exponential low-pass filtered onset energies

This filter is responsible for smoothing the displayed onset energies.
Asymmetric rise and fall constants allow the filter to quickly respond to
increases in onset energy, while slowly responded to decreases.
"""


# Individually normalized energy spike method
# Works well with GAMMA_CORRECTION = True
# This is one of the best visualizations, but doesn't work for everything
def update_leds_6(y):
    """Visualization using per-bin normalized onset energies

    Visualizes onset energies by normalizing each frequency bin individually.
    The normalized bins are then processed and displayed onto the LED strip.

    This function visualizes the onset energies by individually normalizing
    each onset energy bin. The normalized onset bins are then scaled and

    Parameters
    ----------
    y : numpy.array
        Array containing the onset energies that should be visualized.

    """
    y = np.abs(y)**1.25
    # Update normalization constants and then normalize each bin
    _EA_norm.update(y)
    y /= _EA_norm.value
    # Update the onset energy low-pass filter and discard value too dim
    _EA_smooth.update(y)
    _EA_smooth.value[_EA_smooth.value < .1] = 0.0
    # Return the pixels
    pixels = np.copy(_EA_smooth.value)**1.5
    return pixels


_EF_norm = dsp.ExpFilter(np.tile(1.0, config.N_PIXELS), 0.05, 0.9)
_EF_smooth = dsp.ExpFilter(np.tile(1.0, config.N_PIXELS), 0.08, 0.9)
_prev_energy = 0.0


# Individually normalized energy flux
def update_leds_5(y):
    global _prev_energy
    y = np.copy(y)
    EF = np.max(y - _prev_energy, 0.0)
    _prev_energy = np.copy(y)
    _EF_norm.update(EF)
    EF /= _EF_norm.value
    _EF_smooth.update(EF)
    # Cutoff values below 0.1
    _EF_smooth.value[_EF_smooth.value < 0.1] = 0.0
    pixels = np.copy(_EF_smooth.value)
    return pixels


_prev_E = np.tile(.1, config.N_PIXELS)
_EF_N = dsp.ExpFilter(np.tile(.1, config.N_PIXELS), 0.01, 0.9)
def update_leds_5(y):
    global _prev_E
    y = np.copy(y)
    current_E = y**2.0
    EF = current_E - _prev_E
    _prev_E = np.copy(current_E)
    EF[EF < 0.0] = 0.0
    _EF_N.update(EF)
    EF /= _EF_N.value
    EF[current_E < 0.02] = 0.0
    return EF




_energy_norm = dsp.ExpFilter(10.0, alpha_decay=.15, alpha_rise=.9)
_energy_smooth = dsp.ExpFilter(10.0, alpha_decay=0.1, alpha_rise=0.8)


# Modulate brightness by relative average rectified onset flux
def update_leds_4(y):
    global _prev_energy
    energy = np.sum(y**1.0)
    EF = max(energy - _prev_energy, 0.0)
    _prev_energy = energy
    _energy_norm.update(EF)
    _energy_smooth.update(min(EF / _energy_norm.value, 1.0))
    pixels = np.tile(_energy_smooth.value, y.shape[0])
    return pixels


# Energy flux based motion across the LED strip
def update_leds_3(y):
    global pixels, _prev_energy
    y = np.copy(y)
    # Calculate energy flux
    energy = np.sum(y)
    energy_flux = max(energy - _prev_energy, 0)
    _prev_energy = energy
    # Normalize energy flux
    _energy_norm.update(energy_flux)
    # Update and return pixels
    pixels = np.roll(pixels, 1)
    pixels[0] = energy_flux
    return np.copy(pixels)


# Energy based motion across the LED strip
def update_leds_2(y):
    global pixels
    y = np.copy(y)
    # Calculate energy
    energy = np.sum(y**1.5)
    onset_energy.update(energy)
    energy /= onset_energy.value
    # Update and return pixels
    pixels = np.roll(pixels, 1)
    pixels[0] = energy
    return np.copy(pixels)


def update_leds_1(y):
    """Display the raw onset spectrum on the LED strip"""
    return np.copy(y)**0.75


YS_peak = dsp.ExpFilter(1.0, alpha_decay=0.005, alpha_rise=0.95)

def microphone_update(stream):
    global y_roll
    # Retrieve new audio samples and construct the rolling window
    y = np.fromstring(stream.read(samples_per_frame), dtype=np.int16)
    y = y / 2.0**15
    y_roll = np.roll(y_roll, -1, axis=0)
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0)
    # # Calculate onset detection functions
    # SF, NWPD, RCD = dsp.onset(y_data)
    # # Apply Gaussian blur to improve agreement between onset functions
    # SF = gaussian_filter1d(SF, 1.0)
    # NWPD = gaussian_filter1d(NWPD, 1.0)
    # RCD = gaussian_filter1d(RCD, 1.0)
    # # Update and normalize peak followers
    # SF_peak.update(np.max(SF))
    # NWPD_peak.update(np.max(NWPD))
    # RCD_peak.update(np.max(RCD))
    # SF /= SF_peak.value
    # NWPD /= NWPD_peak.value
    # RCD /= RCD_peak.value
    # # Normalize and update onset spectrum
    # onset = SF + NWPD + RCD
    # onset_peak.update(np.max(onset))
    # onset /= onset_peak.value
    # onsets.update(onset)
    # # Map the onset values to LED strip pixels
    # if len(onsets.value) != config.N_PIXELS:
    #     onset_values = interpolate(onsets.value, config.N_PIXELS)
    # else:
    #     onset_values = np.copy(onsets.value)
    # brightness = led_visualization(onset_values)

    XS, YS = dsp.fft(y_data, window=np.hamming)
    YS = YS[XS >= 0.0]
    XS = XS[XS >= 0.0]
    YS = np.atleast_2d(np.abs(YS)).T * dsp.mel_y.T
    YS = np.sum(YS, axis=0)**2.0
    #YS = gaussian_filter1d(YS, 2.0)
    YS = np.diff(YS, n=0)
    YS_peak.update(np.max(YS))
    YS /= YS_peak.value

    if len(YS) != config.N_PIXELS:
        YS = interpolate(YS, config.N_PIXELS)

    #YS = led_visualization(YS)
    YS = led_vis3(YS)

    # Plot the onsets
    #plot_x = np.array(range(1, len(onsets.value) + 1))
    plot_x = np.array(range(1, len(YS) + 1))
    #plot_y = [onsets.value**i for i in np.linspace(2.0, 0.25, config.N_CURVES)]
    plot_y = [YS]
    update_plot_1(plot_x, plot_y)
    app.processEvents()
    print('FPS {:.0f} / {:.0f}'.format(frames_per_second(), config.FPS))


# Create plot and window
app = QtGui.QApplication([])
win = pg.GraphicsWindow('Audio Visualization')
win.resize(300, 200)
win.setWindowTitle('Audio Visualization')
# Create plot 1 containing config.N_CURVES
p1 = win.addPlot(title='Onset Detection Function')
p1.setLogMode(x=False)
curves = []
colors = rainbow(config.N_CURVES) * 255.0
for i in range(config.N_CURVES):
    curve = p1.plot(pen=(colors[i][0], colors[i][1], colors[i][2]))
    curves.append(curve)


# Pixel values for each LED
pixels = np.tile(0.0, config.N_PIXELS)
# Used to colorize the LED strip
color = rainbow(config.N_PIXELS) * 255.0

# Tracks average onset spectral energy
onset_energy = dsp.ExpFilter(1.0, alpha_decay=0.01, alpha_rise=0.65)

# Tracks the location of the spectral median
median = dsp.ExpFilter(val=config.N_SUBBANDS / 2.0,
                               alpha_decay=0.1, alpha_rise=0.1)
# Smooths the decay of the onset detection function
onsets = dsp.ExpFilter(val=np.tile(0.0, (config.N_SUBBANDS)),
                               alpha_decay=0.15, alpha_rise=0.75)
# Peak followers used for normalization
SF_peak = dsp.ExpFilter(1.0, alpha_decay=0.01, alpha_rise=0.99)
NWPD_peak = dsp.ExpFilter(1.0, alpha_decay=0.01, alpha_rise=0.99)
RCD_peak = dsp.ExpFilter(1.0, alpha_decay=0.01, alpha_rise=0.99)
onset_peak = dsp.ExpFilter(0.1, alpha_decay=0.002, alpha_rise=0.5)

# Number of audio samples to read every time frame
samples_per_frame = int(config.MIC_RATE / config.FPS)
# Array containing the rolling audio sample window
y_roll = np.random.rand(config.N_ROLLING_HISTORY, samples_per_frame) / 100.0

# Which LED visualization to use
# update_leds_1 = raw onset spectrum without normalization (GAMMA = True)
# update_leds_2 = energy average chase effect (GAMMA = True)
# update_leds_3 = energy flux chase effect (GAMMA = True)
# update_leds_4 = brightness modulation effect (GAMMA = True)
# update_leds_5 = energy flux normalized per-bin spectrum (GAMMA = True)
# update_leds_6 = energy average normalized per-bin spectrum (GAMMA = True)

# Low pass filter for the LEDs being output to the strip
pixels_filt = dsp.ExpFilter(np.tile(0., (config.N_PIXELS, 3)), .14, .9)


def hyperbolic_tan(x):
    return 1.0 - 2.0 / (np.exp(2.0 * x) + 1.0)


def bloom_peaks(x, width=3, blur_factor=1.0):
    peaks = argrelextrema(x, np.greater)[0]
    y = x * 0.0
    if len(peaks) == 0:
        return y
    for peak in peaks:
        min_idx = max(peak - width, 0)
        max_idx = min(peak + width, len(x) - 1)
        for i in range(min_idx, max_idx):
            y[i] = x[i]
    y = gaussian_filter1d(y, blur_factor)
    return y


# This is the function responsible for updating LED values
# Edit this function to change the visualization
def led_visualization(onset_values):
    # Visualizations that we want to use (normalized to ~[0, 1])
    #pixels_A = update_leds_6(onset_values)
    #pixels_B = update_leds_4(onset_values)
    # Combine the effects by taking the product
    #brightness = pixels_A #* pixels_B
    brightness = update_leds_6(onset_values**2.0)
    brightness = gaussian_filter1d(brightness, 4.0)
    #brightness = hyperbolic_tan(brightness)
    brightness = bloom_peaks(brightness)**2.
    # Combine pixels with color map
    color = rainbow_gen(onset_values.shape[0],
                        speed=1.,
                        center=0.5,
                        width=0.5,
                        f=[1.1, .5, .2]) * 255.0
    color = np.tile(255.0, (config.N_PIXELS, 3))
    # color = rainbow(onset_values.shape[0]) * 255.0
    pixels = (brightness * color.T).T
    pixels = leak_saturated_pixels(pixels)
    pixels = np.clip(pixels, 0., 255.)
    # Apply low-pass filter to the output
    pixels_filt.update(np.copy(pixels))
    # Display values on the LED strip
    led.pixels = np.round(pixels_filt.value).astype(int)
    led.update()
    return brightness


mean_energy = dsp.ExpFilter(0.1, alpha_decay=0.05, alpha_rise=0.05)

def led_vis2(x):
    energy = np.mean(x**.5)
    mean_energy.update(energy)
    energy = energy / mean_energy.value - 1.0
    edge = np.exp(-10 * np.linspace(0, 1, len(x)))
    edge = edge + edge[::-1]
    edge *= max(energy, 0)
    edge /= 2.0

    x = gaussian_filter1d(x, 3.0)
    x = update_leds_6(x)
    red = bloom_peaks(x**1.0, width=1, blur_factor=1.5)
    green = bloom_peaks(x**1.0, width=2, blur_factor=0.5)
    blue = bloom_peaks(x**1.0, width=1, blur_factor=0.5)
    # Set LEDs
    color = np.tile(0.0, (3, config.N_PIXELS))
    color[0, :] = 1.0*edge + red*1.0
    color[1, :] = 1.2*edge + green*1.0
    color[2, :] = 1.5*edge + blue*1.0
    color = color.T * 255.0
    pixels_filt.update(color)
    led.pixels = np.round(pixels_filt.value).astype(int)
    led.update()
    return (color[:, 0] + color[:, 1] + color[:, 2]) / (3. * 255.0)


N = 60
E = []
for i in range(0, N):
    alpha_decay = 0.01 * (float(i + 1) / (N + 1.0))**2.0
    alpha_rise = alpha_decay
    E.append(dsp.ExpFilter(.1, alpha_decay, alpha_rise))

def led_vis3(x):
    energy = np.mean(x**.5)
    pixels = np.tile(0.0, config.N_PIXELS)
    for i in range(N):
        E[i].update(energy)
        pixels[i] = hyperbolic_tan(max(energy / E[i].value - 1.0, 0))

    color = np.tile(0.0, (3, config.N_PIXELS))
    color[0, :] = pixels
    color[1, :] = pixels
    color[2, :] = pixels
    color = color.T * 255.0
    pixels_filt.update(color)
    led.pixels = np.round(pixels_filt.value).astype(int)
    led.update()
    return (color[:, 0] + color[:, 1] + color[:, 2]) / (3. * 255.0)

if __name__ == '__main__':
    led.update()
    microphone.start_stream(microphone_update)
