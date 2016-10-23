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



def rainbow(length, speed=1.0 / 5.0):
    """Returns a rainbow colored array with desired length
        
    Returns a rainbow colored array with shape (length, 3). 
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


_time_prev = time.time() * 1000.0
"""The previous time that the frames_per_second() function was called"""

_fps = dsp.ExponentialFilter(val=config.FPS, alpha_decay=0.01, alpha_rise=0.01)
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
        curves[i].setPen((colors[i][0], colors[i][1], colors[i][2]))
        curves[i].setData(x=x, y=y[i])
    p1.autoRange()
    p1.setRange(yRange=(0, 2.0))


_EA_norm = dsp.ExponentialFilter(np.tile(1e-4, config.N_PIXELS), 0.005, 0.25)
"""Onset energy per-bin normalization constants

This filter is responsible for individually normalizing the onset bin energies.
This is used to obtain per-bin automatic gain control.
"""

_EA_smooth = dsp.ExponentialFilter(np.tile(1.0, config.N_PIXELS),  0.15, 0.80)
"""Asymmetric exponential low-pass filtered onset energies

This filter is responsible for smoothing the displayed onset energies.
Asymmetric rise and fall constants allow the filter to quickly respond to
increases in onset energy, while slowly responded to decreases.
"""

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
        The 
    """
    
    # Scale y to emphasize large spikes and attenuate small changes
    # Exponents < 1.0 emphasize small changes and penalize large spikes
    # Exponents > 1.0 emphasize large spikes and penalize small changes
    y = np.copy(y) ** 1.5

    # Use automatic gain control to normalize bin values
    # Update normalization constants and then normalize each bin
    _EA_norm.update(y)
    y /= _EA_norm.value

    """Force saturated pixels to leak brighness into neighbouring pixels"""

    def smooth():
        for n in range(1, len(y) - 1):
            excess = y[n] - 1.0
            if excess > 0.0:
                y[n] = 1.0
                y[n - 1] += excess / 2.0
                y[n + 1] += excess / 2.0
    
    # Several iterations because the adjacent pixels could also be saturated
    for i in range(6):
        smooth()

    # Update the onset energy low-pass filter and discard value too dim
    _EA_smooth.update(y)
    _EA_smooth.value[_EA_smooth.value < .1] = 0.0

    # If some pixels are too bright, allow saturated pixels to become white
    color = rainbow(config.N_PIXELS) * 255.0
    for i in range(config.N_PIXELS):
        # Update LED strip pixel
        led.pixels[i, :] = np.round(color[i, :] * _EA_smooth.value[i]**1.5)
        # Leak excess red
        excess_red = max(led.pixels[i, 0] - 255, 0)
        led.pixels[i, 1] += excess_red
        led.pixels[i, 2] += excess_red
        # Leak excess green
        excess_green = max(led.pixels[i, 1] - 255, 0)
        led.pixels[i, 0] += excess_green
        led.pixels[i, 2] += excess_green
        # Leak excess blue
        excess_blue = max(led.pixels[i, 2] - 255, 0)
        led.pixels[i, 0] += excess_blue
        led.pixels[i, 1] += excess_blue
    led.update()


_prev_energy = 0.0
_energy_flux = dsp.ExponentialFilter(1.0, alpha_decay=0.05, alpha_rise=0.9)
_EF_norm = dsp.ExponentialFilter(np.tile(1.0, config.N_PIXELS), 0.05, 0.9)
_EF_smooth = dsp.ExponentialFilter(np.tile(1.0, config.N_PIXELS), 0.1, 0.9)


# Individually normalized energy flux
def update_leds_5(y):
    global _prev_energy
    # Scale y
    y = np.copy(y)
    y = y ** 0.5
    
    # Calculate raw energy flux
    # Update previous energy
    # Rectify energy flux
    # Update the normalization constants
    # Normalize the individual energy flux values
    # Smooth the result using another smoothing filter
    EF = y - _prev_energy
    _prev_energy = np.copy(y)
    EF[EF < 0] = 0.0
    _EF_norm.update(EF)
    EF /= _EF_norm.value
    _EF_smooth.update(EF)
    # Cutoff values below 0.1
    _EF_smooth.value[_EF_smooth.value < 0.1] = 0.0

    color = rainbow(config.N_PIXELS) * 255.0
    for i in range(config.N_PIXELS):
        led.pixels[i, :] = np.round(color[i, :] * _EF_smooth.value[i])
        # Share excess red
        excess_red = max(led.pixels[i, 0] - 255, 0)
        led.pixels[i, 1] += excess_red
        led.pixels[i, 2] += excess_red
        # Share excess green
        excess_green = max(led.pixels[i, 1] - 255, 0)
        led.pixels[i, 0] += excess_green
        led.pixels[i, 2] += excess_green
        # Share excess blue
        excess_blue = max(led.pixels[i, 2] - 255, 0)
        led.pixels[i, 0] += excess_blue
        led.pixels[i, 1] += excess_blue
    led.update()


# Modulate brightness of the entire strip with no individual addressing
def update_leds_4(y):
    y = np.copy(y)
    energy = np.sum(y * y)
    _energy_flux.update(energy)
    energy /= _energy_flux.value
    led.pixels = np.round((color * energy)).astype(int)
    led.update()


# Energy flux based motion across the LED strip
def update_leds_3(y):
    global pixels, color, _prev_energy, _energy_flux
    y = np.copy(y)
    # Calculate energy flux
    energy = np.sum(y)
    energy_flux = max(energy - _prev_energy, 0)
    _prev_energy = energy
    # Normalize energy flux
    _energy_flux.update(energy_flux)
    # Update pixels
    pixels = np.roll(pixels, 1)
    color = np.roll(color, 1, axis=0)
    pixels *= 0.99
    pixels[0] = energy_flux

    led.pixels = np.copy(np.round((color.T * pixels).T).astype(int))
    for i in range(config.N_PIXELS):
        # Share excess red
        excess_red = max(led.pixels[i, 0] - 255, 0)
        led.pixels[i, 1] += excess_red
        led.pixels[i, 2] += excess_red
        # Share excess green
        excess_green = max(led.pixels[i, 1] - 255, 0)
        led.pixels[i, 0] += excess_green
        led.pixels[i, 2] += excess_green
        # Share excess blue
        excess_blue = max(led.pixels[i, 2] - 255, 0)
        led.pixels[i, 0] += excess_blue
        led.pixels[i, 1] += excess_blue
    # Update LEDs
    led.update()


# Energy based motion across the LED strip
def update_leds_2(y):
    global pixels, color
    y = np.copy(y)
    # Calculate energy
    energy = np.sum(y**2.0) 
    onset_energy.update(energy)
    energy /= onset_energy.value
    # Update pixels    
    pixels = np.roll(pixels, 1)
    color = np.roll(color, 1, axis=0)
    pixels *= 0.99
    pixels[pixels < 0.0] = 0.0
    pixels[0] = energy
    pixels -= 0.005
    pixels[pixels < 0.0] = 0.0
    led.pixels = np.copy(np.round((color.T * pixels).T).astype(int))
    for i in range(config.N_PIXELS):
        # Share excess red
        excess_red = max(led.pixels[i, 0] - 255, 0)
        led.pixels[i, 1] += excess_red
        led.pixels[i, 2] += excess_red
        # Share excess green
        excess_green = max(led.pixels[i, 1] - 255, 0)
        led.pixels[i, 0] += excess_green
        led.pixels[i, 2] += excess_green
        # Share excess blue
        excess_blue = max(led.pixels[i, 2] - 255, 0)
        led.pixels[i, 0] += excess_blue
        led.pixels[i, 1] += excess_blue
    # Update LEDs
    led.update()



def update_leds_1(y):
    """Display the raw onset spectrum on the LED strip"""
    y = np.copy(y)
    y = y ** 0.5
    color = rainbow(config.N_PIXELS) * 255.0
    
    led.pixels = np.copy(np.round((color.T * y).T).astype(int))
    for i in range(config.N_PIXELS):
        # Share excess red
        excess_red = max(led.pixels[i, 0] - 255, 0)
        led.pixels[i, 1] += excess_red
        led.pixels[i, 2] += excess_red
        # Share excess green
        excess_green = max(led.pixels[i, 1] - 255, 0)
        led.pixels[i, 0] += excess_green
        led.pixels[i, 2] += excess_green
        # Share excess blue
        excess_blue = max(led.pixels[i, 2] - 255, 0)
        led.pixels[i, 0] += excess_blue
        led.pixels[i, 1] += excess_blue
    led.update()


def microphone_update(stream):
    global y_roll, median, onset, SF_peak, NWPD_peak, RCD_peak, onset_peak
    # Retrieve new audio samples and construct the rolling window
    y = np.fromstring(stream.read(samples_per_frame), dtype=np.int16)
    y = y / 2.0**15
    y_roll = np.roll(y_roll, -1, axis=0)
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0)
    # Calculate onset detection functions
    SF, NWPD, RCD = dsp.onset(y_data)
    # Update and normalize peak followers
    SF_peak.update(np.max(SF))
    NWPD_peak.update(np.max(NWPD))
    RCD_peak.update(np.max(RCD))
    SF /= SF_peak.value
    NWPD /= NWPD_peak.value
    RCD /= RCD_peak.value
    # Normalize and update onset spectrum
    onset = SF * NWPD * RCD
    onset_peak.update(np.max(onset))
    onset /= onset_peak.value
    onsets.update(onset)
    # Update the LED strip and resize if necessary
    if len(onsets.value) != config.N_PIXELS:
        onset_values = interpolate(onsets.value, config.N_PIXELS)
    else:
        onset_values = np.copy(onsets.value)
    led_visualization(onset_values)
    # Plot the onsets
    plot_x = np.array(range(1, len(onsets.value) + 1))
    plot_y = [onsets.value**i for i in np.linspace(1, 0.25, config.N_CURVES)]
    update_plot_1(plot_x, plot_y)
    app.processEvents()
    print('{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(SF_peak.value,
                                                          NWPD_peak.value,
                                                          RCD_peak.value,
                                                          onset_peak.value,
                                                          frames_per_second()))


# Create plot and window
app = QtGui.QApplication([])
win = pg.GraphicsWindow('Audio Visualization')
win.resize(800, 600)
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
onset_energy = dsp.ExponentialFilter(1.0, alpha_decay=0.1, alpha_rise=0.99)


# Tracks the location of the spectral median
median = dsp.ExponentialFilter(val=config.N_SUBBANDS / 2.0,
                               alpha_decay=0.1, alpha_rise=0.1)
# Smooths the decay of the onset detection function
onsets = dsp.ExponentialFilter(val=np.tile(0.0, (config.N_SUBBANDS)),
                               alpha_decay=0.05, alpha_rise=0.75)

# Peak followers used for normalization
SF_peak = dsp.ExponentialFilter(1.0, alpha_decay=0.01, alpha_rise=0.99)
NWPD_peak = dsp.ExponentialFilter(1.0, alpha_decay=0.01, alpha_rise=0.99)
RCD_peak = dsp.ExponentialFilter(1.0, alpha_decay=0.01, alpha_rise=0.99)
onset_peak = dsp.ExponentialFilter(0.1, alpha_decay=0.002, alpha_rise=0.1)

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
led_visualization = update_leds_6

if __name__ == '__main__':
    led.update()
    microphone.start_stream(microphone_update)
