from __future__ import print_function
from __future__ import division
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import config
import microphone
import dsp
import led


def a(tau):
    """Returns the ExpFilter alpha value for the given time constant"""
    dT = 1.0 / config.FPS
    return 1.0 - np.exp(-dT / tau)


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


def visualize_scroll(y):
    """Effect that originates in the center and scrolls outwards"""
    global p
    y = np.copy(y)**2.0
    gain.update(y)
    y /= gain.value
    y *= 255.0
    r = int(max(y[:len(y) // 3]))
    g = int(max(y[len(y) // 3: 2 * len(y) // 3]))
    b = int(max(y[2 * len(y) // 3:]))
    # Scrolling effect window
    p = np.roll(p, 1, axis=1)
    p *= 0.98
    p = gaussian_filter1d(p, sigma=0.3)
    # Create new color originating at the center
    p[0, 0] = r
    p[1, 0] = g
    p[2, 0] = b
    return np.concatenate((p[:, ::-1], p), axis=1)



def visualize_scroll(y):
    """Effect that originates in the center and scrolls outwards"""
    global p
    # Shift LED strip
    p = np.roll(p, 1, axis=1)
    p *= 0.98
    # Calculate brightness of origin
    brightness = np.max(y)**4.0
    # Create new color originating at the center
    p[0, 0] = brightness
    p[1, 0] = brightness
    p[2, 0] = brightness
    p = gaussian_filter1d(p, sigma=0.1, order=0)
    output = np.concatenate((p[:, ::-1], p), axis=1)
    output *= rainbow(config.N_PIXELS, speed=1.0 / 5.0) * 255
    return output


def visualize_energy(y):
    """Effect that expands from the center with increasing sound energy"""
    p = np.tile(0, (3, config.N_PIXELS // 2))
    y = y * float((config.N_PIXELS // 2) - 1)
    # Map color channels according to energy in the different freq bands
    scale = 0.9
    r = np.round(np.mean(y[:len(y) // 3]**scale))
    g = np.round(np.mean(y[len(y) // 3: 2 * len(y) // 3]**scale))
    b = np.round(np.mean(y[2 * len(y) // 3:]**scale))
    # Assign color to different frequency regions
    p[0, :int(r)] = 255.0
    p[1, :int(g)] = 255.0
    p[2, :int(b)] = 255.0
    p = _energy.update(p)
    # Apply substantial blur to smooth the edges
    p[0, :] = gaussian_filter1d(p[0, :], sigma=4.0)
    p[1, :] = gaussian_filter1d(p[1, :], sigma=4.0)
    p[2, :] = gaussian_filter1d(p[2, :], sigma=4.0)
    # Set the new pixel value
    return np.concatenate((p[:, ::-1], p), axis=1)


def visualize_spectrum(y):
    """Effect that maps the Mel filterbank frequencies onto the LED strip"""
    _spectrum.update(np.copy(interpolate(y**1.2, config.N_PIXELS // 2)))
    output = rainbow(config.N_PIXELS)
    output *= np.concatenate((_spectrum.value[::-1], _spectrum.value)) 
    return output * 255.0


_time_prev = time.time() * 1000.0
"""Previous time that the frames_per_second() function was called"""
_fps = dsp.ExpFilter(val=config.FPS, decay=a(2), rise=a(2))
"""Filter used to estimate the current FPS"""

_volume = dsp.ExpFilter(1e-12, a(2), rise=a(2))
"""Filter that tracks the average volume"""


_spectrum = dsp.ExpFilter(np.tile(0.1, config.N_PIXELS // 2), a(0.05), a(0.01))
"""Filter for spectrum effect"""
_energy = dsp.ExpFilter(np.tile(.1, (3, config.N_PIXELS // 2)), a(0.1), a(0.1))
"""Filter energy effect"""


_mel_lp = dsp.ExpFilter(np.tile(.1, config.N_FFT_BINS), a(0.1), a(0.01))
"""Filter used to smooth the Mel scale spectral features"""

mel_agc = dsp.ExpFilter(1e-8, decay=a(3), rise=a(1e-3))
"""Filter used for automatic gain control mel spectral features"""
audio_agc = dsp.ExpFilter(1e-8, decay=a(6), rise=a(1e-3))
"""Filter used for automatic gain control of audio input"""

prev_audio_frame = np.tile(1e-10, config.MIC_RATE // config.FPS)
"""Stores data from the previous audio frame"""

visualization_effect = visualize_spectrum
"""Visualization effect to display on the LED strip"""


def microphone_update(stream):
    global prev_audio_frame
    frame_samples = config.MIC_RATE // config.FPS
    try:
        audio_frame = np.fromstring(stream.read(frame_samples), dtype=np.int16)
    except IOError:
        # Intermittent buffer overflows often occur when computer is too slow
        # Process the previous audio frame again (don't have much choice))
        audio_frame = np.copy(prev_audio_frame)
        print('IO error')
    # Volume normalization
    audio_frame = audio_frame / 2.0**15
    vol = np.nanmean(audio_frame ** 2.0)

    audio_frame /= audio_agc.update(np.max(np.abs(audio_frame)))
    # Volume detection
    if _volume.update(vol) < config.MIN_VOLUME_THRESHOLD:
        led.pixels = np.tile(0, (3, config.N_PIXELS))
        led.update()
        if config.USE_GUI:
            app.processEvents()
        print('No volume')
        return
    print(_volume.value - config.MIN_VOLUME_THRESHOLD)

    # Construct overlapping audio frame (50% overlap)
    audio = np.concatenate((prev_audio_frame[frame_samples // 2:], audio_frame))
    prev_audio_frame = audio_frame
    # Extract Mel-scale features from audio data
    mel_features, f_hz = dsp.extract_features(audio)
    mel_features = _mel_lp.update(mel_features)
    # Apply automatic gain control
    #mel_agc.update(np.max(gaussian_filter1d(mel_features, sigma=1.0)))
    mel_agc.update(np.max(mel_features))
    mel_features /= mel_agc.value
    # Map features to a 1D visualization
    led.pixels = visualization_effect(mel_features)
    led.update()
    # Update GUI plots
    if config.USE_GUI:
        mel_curve.setData(x=f_hz, y=mel_features)
        r_curve.setData(y=led.pixels[0])
        g_curve.setData(y=led.pixels[1])
        b_curve.setData(y=led.pixels[2])
        app.processEvents()
    if config.DISPLAY_FPS:
        print('FPS {:.0f} / {:.0f}'.format(frames_per_second(), config.FPS))


if __name__ == '__main__':
    if config.USE_GUI:
        import pyqtgraph as pg
        from pyqtgraph.Qt import QtGui, QtCore
        # Create GUI window
        app = QtGui.QApplication([])
        view = pg.GraphicsView()
        layout = pg.GraphicsLayout(border=(100,100,100))
        view.setCentralItem(layout)
        view.show()
        view.setWindowTitle('Visualization')
        view.resize(800,600)
        # Mel filterbank plot
        fft_plot = layout.addPlot(title='Filterbank Output', colspan=3)
        fft_plot.setRange(yRange=[-0.1, 1.2])
        fft_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        x_data = np.array(range(1, config.N_FFT_BINS + 1))
        mel_curve = pg.PlotCurveItem()
        mel_curve.setData(x=x_data, y=x_data * 0)
        fft_plot.addItem(mel_curve)
        # Visualization plot
        layout.nextRow()
        led_plot = layout.addPlot(title='Visualization Output', colspan=3)
        led_plot.setRange(yRange=[-5, 260])
        led_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        # Pen for each of the color channel curves
        r_pen = pg.mkPen((255, 30, 30, 200), width=4)
        g_pen = pg.mkPen((30, 255, 30, 200), width=4)
        b_pen = pg.mkPen((30, 30, 255, 200), width=4)
        # Color channel curves
        r_curve = pg.PlotCurveItem(pen=r_pen)
        g_curve = pg.PlotCurveItem(pen=g_pen)
        b_curve = pg.PlotCurveItem(pen=b_pen)
        # Define x data
        x_data = np.array(range(1, config.N_PIXELS + 1))
        r_curve.setData(x=x_data, y=x_data * 0)
        g_curve.setData(x=x_data, y=x_data * 0)
        b_curve.setData(x=x_data, y=x_data * 0)
        # Add curves to plot
        led_plot.addItem(r_curve)
        led_plot.addItem(g_curve)
        led_plot.addItem(b_curve)
        # Frequency range label
        freq_label = pg.LabelItem('')
        # Frequency slider
        def freq_slider_change(tick):
            minf = freq_slider.tickValue(0)**2.0 * (config.MIC_RATE / 2.0)
            maxf = freq_slider.tickValue(1)**2.0 * (config.MIC_RATE / 2.0)
            t = 'Frequency range: {:.0f} - {:.0f} Hz'.format(minf, maxf)
            freq_label.setText(t)
            config.MIN_FREQUENCY = minf
            config.MAX_FREQUENCY = maxf
            # dsp.create_mel_bank()
        freq_slider = pg.TickSliderItem(orientation='bottom', allowAdd=False)
        freq_slider.addTick((config.MIN_FREQUENCY / (config.MIC_RATE / 2.0))**0.5)
        freq_slider.addTick((config.MAX_FREQUENCY / (config.MIC_RATE / 2.0))**0.5)
        freq_slider.tickMoveFinished = freq_slider_change
        freq_label.setText('Frequency range: {} - {} Hz'.format(
            config.MIN_FREQUENCY,
            config.MAX_FREQUENCY))
        # Effect selection
        active_color = '#16dbeb'
        inactive_color = '#FFFFFF'
        def energy_click(x):
            global visualization_effect
            visualization_effect = visualize_energy
            energy_label.setText('Energy', color=active_color)
            scroll_label.setText('Scroll', color=inactive_color)
            spectrum_label.setText('Spectrum', color=inactive_color)
        def scroll_click(x):
            global visualization_effect
            visualization_effect = visualize_scroll
            energy_label.setText('Energy', color=inactive_color)
            scroll_label.setText('Scroll', color=active_color)
            spectrum_label.setText('Spectrum', color=inactive_color)
        def spectrum_click(x):
            global visualization_effect
            visualization_effect = visualize_spectrum
            energy_label.setText('Energy', color=inactive_color)
            scroll_label.setText('Scroll', color=inactive_color)
            spectrum_label.setText('Spectrum', color=active_color)
        # Create effect "buttons" (labels with click event)
        energy_label = pg.LabelItem('Energy')
        scroll_label = pg.LabelItem('Scroll')
        spectrum_label = pg.LabelItem('Spectrum')
        energy_label.mousePressEvent = energy_click
        scroll_label.mousePressEvent = scroll_click
        spectrum_label.mousePressEvent = spectrum_click
        energy_click(0)
        # Layout
        layout.nextRow()
        layout.addItem(freq_label, colspan=3)
        layout.nextRow()
        layout.addItem(freq_slider, colspan=3)
        layout.nextRow()
        layout.addItem(energy_label)
        layout.addItem(scroll_label)
        layout.addItem(spectrum_label)
    # Initialize LEDs
    led.update()
    # Start listening to live audio stream
    microphone.start_stream(microphone_update)
