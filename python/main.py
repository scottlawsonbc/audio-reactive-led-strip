from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function

import inspect
import time
import imp
import numpy as np
from matplotlib import cm
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

past_N = 256
past_spectrum = np.tile(0.0, (config.N_FFT_BINS * 2, past_N, 3))


past_frames = 1
prev_frames = np.tile(0.0, (past_frames, config.MIC_RATE // config.FPS))
"""Contains the previous batch of audio frames"""

rolling_window = None
"""Contains rolling audio window frames"""

gui_settings_dict = {}
"""Dictionary containing the values of the GUI setting controls"""

gui_settings_changed_flag = False
"""Flag for indicating that GUI settings have been changed"""


def terminate():
    """Shut things down properly before exiting"""
    audio.end_stream()
    led.pixels *= 0
    led.update()
    raise SystemExit


def audio_visualization(audio_frames):
    """Maps audio_frames input to an LED strip visualization"""
    power_spectrum = features.fft_power_spectrum(audio_frames)
    frequency = features.spectral_rolloff(power_spectrum)
    # print(frequency
    # We apply coarse rounding so that we can memoize the filterbank
    frequency = np.ceil(frequency / 50.0) * 50.0
    config.MAX_FREQ = frequency
    effect_function = getattr(visualize, current_effect)
    led.pixels = effect_function(audio_frames) * 255
    led.update()


def update_rolling_window():
    global prev_frames
    global rolling_window
    frame_count = config.MIC_RATE // config.FPS
    frames_available = audio.stream.get_read_available()
    # We only want frames that are available immediately
    if frames_available >= frame_count:
        try:
            frames = np.fromstring(audio.stream.read(frame_count), np.float32)
        except OSError as e:
            if e.errno == -9981:
                print('Audio buffer overlow. FPS too high?')
                audio.start_stream()
                return
            else:
                raise
        rolling_window = np.concatenate((prev_frames[0, frame_count // 2:], frames))
        prev_frames = np.roll(prev_frames, 1, axis=0)
        prev_frames[0] = frames


def roundup(val, multiple):
    remainder = val % multiple
    if remainder == 0:
        return val
    else:
        return val + multiple - remainder  


def update_settings():
    """Called when user changes a GUI setting"""
    global current_effect
    global prev_frames
    global past_spectrum
    bins = gui_settings_dict['fft_bins']

    gui_settings_dict['fft_bins'] = roundup(bins, gui_settings_dict['pixels'])
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
    # Reset the rolling audio window
    prev_frames = np.tile(0.0, (past_frames, config.MIC_RATE // config.FPS))
    # past_spectrum = np.tile(0.0, (past_N, config.N_PIXELS, 3))
    past_spectrum = np.tile(0.0, (config.N_FFT_BINS * 2, past_N, 3))
    print('Settings changed')


def guiSettingsChanged(settings_dict):
    """Update the settings because the user changed a setting in the GUI"""
    global gui_settings_dict
    global gui_settings_changed_flag
    gui_settings_dict = settings_dict
    gui_settings_changed_flag = True


color_maps_mpl = [
    'Blues',
    'BuGn',
    'BuPu',
    'GnBu',
    'Greens',
    'Greys',
    'Oranges',
    'OrRd',
    'PuBu',
    'PuBuGn',
    'PuRd',
    'Purples',
    'RdPu',
    'Reds',
    'YlGn',
    'YlGnBu',
    'YlOrBr',
    'YlOrRd']


if __name__ == '__main__':
    # Create and show the GUI
    if config.USE_GUI:
        initial_settings = {
            'fps': config.FPS,
            'pixels': config.N_PIXELS,
            'effect_index': 0,
            'cmap_index': 0,
            'rise': 1,
            'fall': 1,
            'min_freq': config.MIN_FREQ,
            'max_freq': config.MAX_FREQ,
            'fft_bins': config.N_FFT_BINS,
            'cmap': config.CMAP
        }
        # Create GUI object
        app = QtGui.QApplication([])
        win = gui.MainWindow(initial_settings)
        win.settingsUpdated.connect(guiSettingsChanged)
        win.closing.connect(terminate)
        # Effect list is automatically generated
        # All 'public' functions in visualize.py are considered effects
        effects = inspect.getmembers(visualize, inspect.isfunction)
        effects = np.array(effects)[:, 0]
        effects = [e for e in effects if not e.startswith('_')]
        win.effect.addItems(effects)
        print(effects)
        # Populate list of colormaps
        # maps = [m for m in cm.datad if not m.endswith("_r")]
        maps = [m for m in cm.datad]
        # win.colormap.addItems(maps)
        win.colormap.addItems(color_maps_mpl)
        win.settingsChanged(0)
        win.show()
        win.plot1.hide()

    fps_filter = dsp.RealTimeExpFilter(config.FPS, rise=0.25, fall=0.25)
    t = time.time()
    audio.start_stream()
    time.sleep(0.1)
    effect_idx = 0
    effect_switch = False

    # Used to limit the refresh rate of the plot
    # This improves the audio processing framerate significantly
    last_plot_update_time = time.time()

    while True:
        # FPS
        dt = time.time() - t
        t += dt
        fps = fps_filter.update(dt**-1.0)

        if int(time.time()) % 15:
            if effect_switch:
                effect_idx = np.random.random_integers(0, len(color_maps_mpl) - 1)
                print('changed effect')

                visualize.cmap = cm.get_cmap(color_maps_mpl[effect_idx % len(color_maps_mpl)])
                effect_switch = False
        else:
            effect_switch = True

        if config.USE_GUI:
            win.fpsLabel.setText('{:.0f}'.format(fps))
            if gui_settings_changed_flag:
                gui_settings_changed_flag = False
                audio.end_stream()
                update_settings()
                audio.start_stream()

        update_rolling_window()
        if rolling_window is not None:
            audio_visualization(rolling_window)
            past_spectrum = np.roll(past_spectrum, 1, axis=1)
            spec = features.auto_spectrum(rolling_window)
            spec = visualize._apply_colormap(spec)
            spec = np.concatenate((spec[:, ::-1], spec), axis=1)
            past_spectrum[:, 0] = spec.T

            if time.time() - last_plot_update_time > 1. / 30.:
                win.img.setImage(past_spectrum)
                last_plot_update_time = time.time()

        time.sleep(1e-3)
        app.processEvents()
    audio.end_stream()
