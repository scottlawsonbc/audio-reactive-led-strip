from __future__ import print_function
from __future__ import division
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import config
import microphone
import dsp
import led
if config.USE_GUI:
    import gui

_time_prev = time.time() * 1000.0
"""The previous time that the frames_per_second() function was called"""

_fps = dsp.ExpFilter(val=config.FPS, alpha_decay=0.002, alpha_rise=0.002)
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


r_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.04, alpha_rise=0.4)
g_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.15, alpha_rise=0.99)
b_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.25, alpha_rise=0.99)
p_filt = dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.2, alpha_rise=0.99)
p = np.tile(1.0, (3, config.N_PIXELS // 2))
gain = dsp.ExpFilter(np.tile(0.01, config.N_FFT_BINS),
                     alpha_decay=0.001, alpha_rise=0.99)


def visualize_scroll(y):
    """Effect that originates in the center and scrolls outwards"""
    global p
    y = np.copy(y)**1.0
    gain.update(y)
    y /= gain.value
    y *= 255.0
    r = int(max(y[:len(y) // 3]))
    g = int(max(y[len(y) // 3: 2 * len(y) // 3]))
    b = int(max(y[2 * len(y) // 3:]))
    # Scrolling effect window
    p = np.roll(p, 1, axis=1)
    p *= 0.98
    # p = gaussian_filter1d(p, sigma=0.2)
    # Create new color originating at the center
    p[0, 0] = r
    p[1, 0] = g
    p[2, 0] = b
    # Update the LED strip
    led.pixels = np.concatenate((p[:, ::-1], p), axis=1)
    led.update()
    if config.USE_GUI:
        # Update the GUI plots
        GUI.curve[0][0].setData(y=np.concatenate((p[0, :][::-1], p[0, :])))
        GUI.curve[0][1].setData(y=np.concatenate((p[1, :][::-1], p[1, :])))
        GUI.curve[0][2].setData(y=np.concatenate((p[2, :][::-1], p[2, :])))


def visualize_energy(y):
    """Effect that expands from the center with increasing sound energy"""
    global p
    y = np.copy(y)**2.0
    gain.update(y)
    y /= gain.value
    # Scale by the width of the LED strip
    y *= float((config.N_PIXELS // 2) - 1)
    # Map color channels according to energy in the different freq bands
    scale = 0.9
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
    # Apply substantial blur to smooth the edges
    p[0, :] = gaussian_filter1d(p[0, :], sigma=4.0)
    p[1, :] = gaussian_filter1d(p[1, :], sigma=4.0)
    p[2, :] = gaussian_filter1d(p[2, :], sigma=4.0)
    # Set the new pixel value
    led.pixels = np.concatenate((p[:, ::-1], p), axis=1)
    led.update()
    if config.USE_GUI:
        # Update the GUI plots
        GUI.curve[0][0].setData(y=np.concatenate((p[0, :][::-1], p[0, :])))
        GUI.curve[0][1].setData(y=np.concatenate((p[1, :][::-1], p[1, :])))
        GUI.curve[0][2].setData(y=np.concatenate((p[2, :][::-1], p[2, :])))


def visualize_spectrum(y):
    """Effect that maps the Mel filterbank frequencies onto the LED strip"""
    y = np.copy(interpolate(y, config.N_PIXELS // 2))
    # Blur the color channels with different strengths
    r = gaussian_filter1d(y, sigma=1., order=0)
    g = gaussian_filter1d(y, sigma=1., order=0)
    b = gaussian_filter1d(y, sigma=1., order=0)
    # Update temporal filters
    r_filt.update(r)
    g_filt.update(g)
    b_filt.update(b)
    # Pixel values
    pixel_r = np.concatenate((r_filt.value[::-1], r_filt.value)) * 255.0
    pixel_g = np.concatenate((g_filt.value[::-1], g_filt.value)) * 255.0
    pixel_b = np.concatenate((b_filt.value[::-1], b_filt.value)) * 255.0
    # Update the LED strip values
    led.pixels[0, :] = pixel_r
    led.pixels[1, :] = pixel_g
    led.pixels[2, :] = pixel_b
    led.update()
    if config.USE_GUI:
        # Update the GUI plots
        GUI.curve[0][0].setData(y=pixel_r)
        GUI.curve[0][1].setData(y=pixel_g)
        GUI.curve[0][2].setData(y=pixel_b)


mel_gain = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.01, alpha_rise=0.99)
volume = dsp.ExpFilter(config.MIN_VOLUME_THRESHOLD,
                       alpha_decay=0.02, alpha_rise=0.02)

# Keeps track of the number of buffer overflows
# Lots of buffer overflows could mean that FPS is set too high
buffer_overflows = 1


def microphone_update(stream):
    global y_roll, prev_rms, prev_exp
    # Retrieve and normalize the new audio samples
    try:
        y = np.fromstring(stream.read(samples_per_frame), dtype=np.int16)
    except IOError:
        y = y_roll[config.N_ROLLING_HISTORY - 1, :]
        global buffer_overflows
        print('Buffer overflows: {0}'.format(buffer_overflows))
        buffer_overflows += 1
    # Normalize samples between 0 and 1
    y = y / 2.0**15
    # Construct a rolling window of audio samples
    y_roll = np.roll(y_roll, -1, axis=0)
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0)
    volume.update(np.nanmean(y_data ** 2))

    if volume.value < config.MIN_VOLUME_THRESHOLD:
        print('No audio input. Volume below threshold. Volume:', volume.value)
        led.pixels = np.tile(0, (3, config.N_PIXELS))
        led.update()
    else:
        # Transform audio input into the frequency domain
        XS, YS = dsp.fft(y_data, window=np.hamming)
        # Remove half of the FFT data because of symmetry
        YS = YS[:len(YS) // 2]
        XS = XS[:len(XS) // 2]
        # Construct a Mel filterbank from the FFT data
        YS = np.atleast_2d(np.abs(YS)).T * dsp.mel_y.T
        # Scale data to values more suitable for visualization
        YS = np.sum(YS, axis=0)**2.0
        mel = YS**0.5
        mel = gaussian_filter1d(mel, sigma=1.0)
        # Normalize the Mel filterbank to make it volume independent
        mel_gain.update(np.max(mel))
        mel = mel / mel_gain.value
        # Visualize the filterbank output
        visualization_effect(mel)
    if config.USE_GUI:
        GUI.app.processEvents()
    if config.DISPLAY_FPS:
        print('FPS {:.0f} / {:.0f}'.format(frames_per_second(), config.FPS))


# Number of audio samples to read every time frame
samples_per_frame = int(config.MIC_RATE / config.FPS)

# Array containing the rolling audio sample window
y_roll = np.random.rand(config.N_ROLLING_HISTORY, samples_per_frame) / 1e16

visualization_effect = visualize_energy
"""Visualization effect to display on the LED strip"""

if __name__ == '__main__':
    if config.USE_GUI:
        import pyqtgraph as pg
        # Create GUI plot for visualizing LED strip output
        GUI = gui.GUI(width=800, height=400, title='Audio Visualization')
        GUI.add_plot('Color Channels')
        r_pen = pg.mkPen((255, 30, 30, 200), width=6)
        g_pen = pg.mkPen((30, 255, 30, 200), width=6)
        b_pen = pg.mkPen((30, 30, 255, 200), width=6)
        GUI.add_curve(plot_index=0, pen=r_pen)
        GUI.add_curve(plot_index=0, pen=g_pen)
        GUI.add_curve(plot_index=0, pen=b_pen)
        GUI.plot[0].setRange(xRange=(0, config.N_PIXELS), yRange=(-5, 275))
        GUI.curve[0][0].setData(x=range(config.N_PIXELS))
        GUI.curve[0][1].setData(x=range(config.N_PIXELS))
        GUI.curve[0][2].setData(x=range(config.N_PIXELS))
        # Add ComboBox for effect selection
        effect_list = {
            'Scroll effect': visualize_scroll, 
            'Spectrum effect': visualize_spectrum,
            'Energy effect': visualize_energy
            }
        effect_combobox = pg.ComboBox(items=effect_list)
        def effect_change():
            global visualization_effect
            visualization_effect = effect_combobox.value()
        effect_combobox.setValue(visualization_effect)
        effect_combobox.currentIndexChanged.connect(effect_change)
        GUI.layout.addWidget(effect_combobox)
    # Initialize LEDs
    led.update()
    # Start listening to live audio stream
    microphone.start_stream(microphone_update)
