from __future__ import print_function
from __future__ import division
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import config
import microphone
import dsp
import led
import gui


_time_prev = time.time() * 1000.0
"""The previous time that the frames_per_second() function was called"""

_fps = dsp.ExpFilter(val=config.FPS, alpha_decay=0.01, alpha_rise=0.01)
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


def normalize(f):
    """Returns a histogram normalized numpy.array"""
    lmin = float(f.min())
    lmax = float(f.max())
    return np.floor((f - lmin) / (lmax - lmin) * 255.0)


r_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS),
                       alpha_decay=0.075, alpha_rise=0.6)
g_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS),
                       alpha_decay=0.25, alpha_rise=0.9)
b_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS),
                       alpha_decay=0.5, alpha_rise=0.95)


def visualize(y):
    y = np.copy(interpolate(y, config.N_PIXELS)) * 255.0
    # Blur the color channels with different strengths
    r = gaussian_filter1d(y, sigma=0.15)
    g = gaussian_filter1d(y, sigma=2.0)
    b = gaussian_filter1d(y, sigma=0.0)
    # Take the geometric mean of the raw and normalized histograms
    r = np.sqrt(r * normalize(r))
    g = np.sqrt(g * normalize(g))
    b = np.sqrt(b * normalize(b))
    # Update the low pass filters for each color channel
    r_filt.update(r)
    g_filt.update(g)
    b_filt.update(b)
    # Update the LED strip values
    led.pixels[:, 0] = r_filt.value
    led.pixels[:, 1] = g_filt.value
    led.pixels[:, 2] = b_filt.value
    # Update the GUI plots
    GUI.curve[0][0].setData(x=range(len(r_filt.value)), y=r_filt.value)
    GUI.curve[0][1].setData(x=range(len(g_filt.value)), y=g_filt.value)
    GUI.curve[0][2].setData(x=range(len(b_filt.value)), y=b_filt.value)
    led.update()


mel_gain = dsp.ExpFilter(np.tile(1e-1, config.N_PIXELS),
                         alpha_decay=0.01, alpha_rise=0.99)
volume = dsp.ExpFilter(config.MIN_VOLUME_THRESHOLD,
                       alpha_decay=0.02, alpha_rise=0.02)


def microphone_update(stream):
    global y_roll
    # Normalize new audio samples
    y = np.fromstring(stream.read(samples_per_frame), dtype=np.int16)
    y = y / 2.0**15
    # Construct a rolling window of audio samples
    y_roll = np.roll(y_roll, -1, axis=0)
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0)
    volume.update(np.nanmean(y_data ** 2))

    if volume.value < config.MIN_VOLUME_THRESHOLD:
        print('No audio input. Volume below threshold. Volume:', volume.value)
        visualize(np.tile(0.0, config.N_PIXELS))
    else:
        XS, YS = dsp.fft(y_data, window=np.hamming)
        # Construct Mel filterbank
        YS = YS[XS >= 0.0]
        XS = XS[XS >= 0.0]
        YS = np.atleast_2d(np.abs(YS)).T * dsp.mel_y.T
        YS = np.sum(YS, axis=0)**2.0
        mel = np.concatenate((YS[::-1], YS))
        mel = interpolate(mel, config.N_PIXELS)
        mel = (mel)**2.
        mel_gain.update(mel)
        mel = mel / mel_gain.value
        visualize(mel)

    GUI.app.processEvents()
    print('FPS {:.0f} / {:.0f}'.format(frames_per_second(), config.FPS))


# Number of audio samples to read every time frame
samples_per_frame = int(config.MIC_RATE / config.FPS)

# Array containing the rolling audio sample window
y_roll = np.random.rand(config.N_ROLLING_HISTORY, samples_per_frame) / 1e16


if __name__ == '__main__':
    import pyqtgraph as pg
    GUI = gui.GUI(width=800, height=400, title='Audio Visualization')
    # Audio plot
    GUI.add_plot('Color Channels')
    r_pen = pg.mkPen((255, 30, 30, 200), width=3)
    g_pen = pg.mkPen((30, 255, 30, 200), width=3)
    b_pen = pg.mkPen((30, 30, 255, 200), width=3)
    GUI.add_curve(plot_index=0, pen=r_pen)
    GUI.add_curve(plot_index=0, pen=g_pen)
    GUI.add_curve(plot_index=0, pen=b_pen)
    GUI.plot[0].setRange(xRange=(0, 60), yRange=(-40, 275))
    # Initialize LEDs
    led.update()
    # Start listening to live audio stream
    microphone.start_stream(microphone_update)
