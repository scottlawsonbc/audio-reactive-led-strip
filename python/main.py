from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function

import time
import imp
import numpy as np
from scipy import signal
import config
import led
import dsp
import features
import visualize
import audio
if config.USE_GUI:
    from pyqtgraph.Qt import QtGui
    import gui

current_effect = 'Spectrum'
"""Currently selected visualization effect"""

prev_frames = np.array([0.0])
"""Contains the previous batch of audio frames"""

rolling_window = np.array([0.0])
"""Contains rolling audio window frames"""

gui_settings_dict = {}
"""Dictionary containing the values of the GUI setting controls"""

gui_settings_changed_flag = False
"""Flag for indicating that GUI settings have been changed"""


p1c1_y = np.arange(0, 1)
p1c2_y = np.arange(0, 1)
p1c3_y = np.arange(0, 1)
p2c1_y = np.arange(0, 1)
p2c2_y = np.arange(0, 1)
p2c3_y = np.arange(0, 1)
"""Used for passing plot data between threads"""


def terminate():
    """Shut things down properly before exiting"""
    audio.end_stream()
    led.pixels *= 0
    led.update()
    raise SystemExit


def init_gui_plots():
    global p1c1, p1c2, p1c3
    global p2c1, p2c2, p2c3
    # Plot 1 Configuration
    win.plot1.setRange(yRange=[-5, 260])
    win.plot1.disableAutoRange(axis=gui.pg.ViewBox.YAxis)
    r = gui.pg.mkPen((255, 30, 30, 200), width=4)
    g = gui.pg.mkPen((30, 255, 30, 200), width=4)
    b = gui.pg.mkPen((30, 30, 255, 200), width=4)
    p1c1 = gui.pg.PlotCurveItem(pen=r)
    p1c2 = gui.pg.PlotCurveItem(pen=g)
    p1c3 = gui.pg.PlotCurveItem(pen=b)
    win.plot1.addItem(p1c1)
    win.plot1.addItem(p1c2)
    win.plot1.addItem(p1c3)
    # Plot 2 Configuration
    win.plot2.setRange(yRange=[-5, 260])
    win.plot2.disableAutoRange(axis=gui.pg.ViewBox.YAxis)
    r = gui.pg.mkPen((255, 30, 30, 200), width=4)
    g = gui.pg.mkPen((30, 255, 30, 200), width=4)
    b = gui.pg.mkPen((30, 30, 255, 200), width=4)
    p2c1 = gui.pg.PlotCurveItem(pen=r)
    p2c2 = gui.pg.PlotCurveItem(pen=g)
    p2c3 = gui.pg.PlotCurveItem(pen=b)

    win.plot2.addItem(p2c1)
    win.plot2.addItem(p2c2)
    win.plot2.addItem(p2c3)


def audio_visualization(audio_frames):
    global p1c1_y, p1c2_y, p1c3_y
    global p2c1_y, p2c2_y, p2c3_y
    """Maps audio_frames input to an LED strip visualization"""
    audio_frames = audio_frames / 2.0**15
    freq_data = features.mel_spectrum(audio_frames)
    effect_function = getattr(visualize, current_effect.lower())
    led_output = effect_function(freq_data, audio_frames) * 255
    led.pixels = led_output
    led.update()

    p2c1_y = led_output[0, :]
    p2c2_y = led_output[1, :]
    p2c3_y = led_output[2, :]


def update_rolling_window():
    global prev_frames
    global rolling_window
    frame_count = config.MIC_RATE // config.FPS
    frames_available = audio.stream.get_read_available()
    # We only want frames that are available immediately
    if frames_available >= frame_count:
        frames = np.fromstring(audio.stream.read(frame_count), np.float32)
        frames = signal.detrend(frames)
        rolling_window = np.concatenate((prev_frames, frames))
        prev_frames = frames[frame_count // 2:]


def update_settings():
    global current_effect
    # Update settings values
    current_effect = gui_settings_dict['effect']
    config.set_config_from_dict(gui_settings_dict)
    config.write()
    # Reload imports to reinitialize with updated settings values
    # Feels a bit hacky but it works.
    imp.reload(led)
    imp.reload(dsp)
    imp.reload(features)
    imp.reload(visualize)
    if not gui_settings_dict['show_plot']:
        for widget in win.plot1.children():
            if isinstance(widget, gui.pg.PlotCurveItem):
                widget.clear()
        for widget in win.plot2.children():
            if isinstance(widget, gui.pg.PlotCurveItem):
                widget.clear()
        app.processEvents()

    print('Settings changed')


def guiSettingsChanged(settings_dict):
    """Update the settings because the user changed a setting in the GUI"""
    global gui_settings_dict
    global gui_settings_changed_flag
    gui_settings_dict = settings_dict
    gui_settings_changed_flag = True


if __name__ == '__main__':
    # Create and show the GUI
    if config.USE_GUI:
        effect_index = 0  # list(effects.keys()).index(current_effect)
        initial_settings = {
            'fps': config.FPS,
            'pixels': config.N_PIXELS,
            'effect_index': effect_index,
            'rise': 1,
            'fall': 1,
            'min_freq': config.MIN_FREQ,
            'max_freq': config.MAX_FREQ,
            'fft_bins': config.N_FFT_BINS
        }
        app = QtGui.QApplication([])

        win = gui.MainWindow(initial_settings)
        win.settingsUpdated.connect(guiSettingsChanged)
        win.closing.connect(terminate)
        win.settingsChanged(0)
        init_gui_plots()
        win.show()


    fps_filter = dsp.RealTimeExpFilter(config.FPS, rise=0.25, fall=0.25)
    t = time.time()
    audio.start_stream()

    while True:
        if config.USE_GUI:
            # FPS counter
            fps = fps_filter.update(1. / (time.time() - t))
            t = time.time()
            win.fpsLabel.setText('FPS: {:.0f}'.format(fps))
            if gui_settings_changed_flag:
                gui_settings_changed_flag = False
                audio.end_stream()
                update_settings()
                audio.start_stream()
        update_rolling_window()
        audio_visualization(rolling_window)

        if gui_settings_dict['show_plot']:
            x = np.arange(len(p2c1_y))
            p2c1.setData(x=x, y=p2c1_y)
            p2c2.setData(x=x, y=p2c2_y)
            p2c3.setData(x=x, y=p2c3_y)



        time.sleep(1e-3) # For numerical stability
        app.processEvents()
    audio.end_stream()
