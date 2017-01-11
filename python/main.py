from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function

import time
import imp
import numpy as np
import pyaudio
import config
import led
import dsp
import features
import visualize
import microphone
if config.USE_GUI:
    from pyqtgraph.Qt import QtGui
    import gui2

effects = {
    'Spectrum': visualize.spectrum,
    'Scroll': visualize.scroll,
    'Energy': visualize.energy
}

current_effect = 'Spectrum'
"""Currently selected visualization effect"""

prev_audio = np.array([0.0])
"""Previous audio frames used to construct a rolling window"""

using_stream_flag = False
"""Flag that tells the GUI thread when it isn't safe to close the stream"""

rolling_window = np.array([0])
"""Rolling audio window"""

p1c1_y = np.arange(0, 1)
p1c2_y = np.arange(0, 1)
p1c3_y = np.arange(0, 1)
p2c1_y = np.arange(0, 1)
p2c2_y = np.arange(0, 1)
p2c3_y = np.arange(0, 1)
"""Used for passing plot data between threads"""


def terminate():
    """Shut things down properly before exiting"""
    microphone.close_stream()
    led.pixels *= 0
    led.update()
    raise SystemExit


def init_gui_plots():
    global p1c1, p1c2, p1c3
    global p2c1, p2c2, p2c3
    # Plot 1 Configuration
    win.plot1.setRange(yRange=[-5, 260])
    win.plot1.disableAutoRange(axis=gui2.pg.ViewBox.YAxis)
    r = gui2.pg.mkPen((255, 30, 30, 200), width=4)
    g = gui2.pg.mkPen((30, 255, 30, 200), width=4)
    b = gui2.pg.mkPen((30, 30, 255, 200), width=4)
    p1c1 = gui2.pg.PlotCurveItem(pen=r)
    p1c2 = gui2.pg.PlotCurveItem(pen=g)
    p1c3 = gui2.pg.PlotCurveItem(pen=b)
    win.plot1.addItem(p1c1)
    win.plot1.addItem(p1c2)
    win.plot1.addItem(p1c3)
    # Plot 2 Configuration
    win.plot2.setRange(yRange=[-5, 260])
    win.plot2.disableAutoRange(axis=gui2.pg.ViewBox.YAxis)
    r = gui2.pg.mkPen((255, 30, 30, 200), width=4)
    g = gui2.pg.mkPen((30, 255, 30, 200), width=4)
    b = gui2.pg.mkPen((30, 30, 255, 200), width=4)
    p2c1 = gui2.pg.PlotCurveItem(pen=r)
    p2c2 = gui2.pg.PlotCurveItem(pen=g)
    p2c3 = gui2.pg.PlotCurveItem(pen=b)
    win.plot2.addItem(p2c1)
    win.plot2.addItem(p2c2)
    win.plot2.addItem(p2c3)


def audio_visualization(audio):
    global p1c1_y, p1c2_y, p1c3_y
    global p2c1_y, p2c2_y, p2c3_y
    """Maps audio input to an LED strip visualization"""
    audio = audio / 2.0**15
    filter_bank_output = features.mel_spectrum(audio)
    led_output = effects[current_effect](filter_bank_output)
    led.pixels = led_output
    led.update()

    p2c1_y = led_output[0, :]
    p2c2_y = led_output[1, :]
    p2c3_y = led_output[2, :]


def callback(in_data, frame_count, time_info, flag):
    global using_stream_flag
    global prev_audio
    global rolling_window
    using_stream_flag = True

    # Rolling audio window
    audio = np.fromstring(in_data, np.float32)
    rolling_window = np.concatenate((prev_audio, audio))
    prev_audio = audio[frame_count // 2:]

    using_stream_flag = False
    return (audio, pyaudio.paContinue)


def settings_updated(settings_dict):
    """Update the settings because the user changed a setting in the GUI"""
    global current_effect
    current_effect = settings_dict['effect']
    while using_stream_flag:
        pass
    microphone.close_stream()

    # Update config with new settings
    config.set_config_from_dict(settings_dict)
    config.write()
    # Reload modules to prevent errors
    # It's hacky but it works

    imp.reload(led)
    imp.reload(dsp)
    imp.reload(features)
    imp.reload(visualize)
    imp.reload(visualize)
    # Restart the audio stream
    microphone.start_stream(callback=callback)
    print('Settings changed. Audio stream has been restarted.')


if __name__ == '__main__':
    # Create the GUI window
    if config.USE_GUI:
        effect_index = list(effects.keys()).index(current_effect)
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

        win = gui2.MainWindow(initial_settings)
        win.settingsUpdated.connect(settings_updated)
        win.closing.connect(terminate)
        win.settingsChanged(0)
        init_gui_plots()
        win.show()

    t = time.time()

    microphone.start_stream(callback=callback)
    while True:
        # Visualization and output
        audio_visualization(rolling_window)

        #x1 = np.arange(len(p1c1_y))
        #x2 = np.arange(len(p2c1_y))

        # p1c1.setData(x=x1, y=p1c1_y)
        # p1c2.setData(x=x1, y=p1c2_y)
        # p1c3.setData(x=x1, y=p1c3_y)

        # p2c1.setData(x=x2, y=p2c1_y)
        # p2c2.setData(x=x2, y=p2c2_y)
        # p2c3.setData(x=x2, y=p2c3_y)

        print(1 / (time.time() - t))
        t = time.time()

        #time.sleep(0.00)
        app.processEvents()
        
    microphone.close_stream()
