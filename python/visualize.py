from __future__ import print_function
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import dsp
import led
import microphone as mic

# Settings for beat detection
dsp.ys_beat_threshold = 1.8
dsp.ys_variance_threshold = 0.1

# List of beats currently visible on the LED strip
visible_beats = np.array([])

class Beat:
    def __init__(self, pixels, speed):
        self.pixels = pixels
        self.speed = float(speed)
        self.zeros = np.zeros(len(pixels))
        self.iteration = 0

    def update_pixels(self):
        self.iteration += 1
        self.speed = max(0.95 * self.speed, 1.0)
        self.pixels = np.roll(self.pixels, int(self.speed))
        self.pixels[:int(self.speed)] = 0.0
        s = self.iteration / led.N_pixels
        self.pixels = gaussian_filter1d(self.pixels, s, mode='constant')
        self.pixels = np.round(self.pixels, decimals=1)

    def finished(self):
        return (self.pixels == self.zeros).all()


prev_dir = True
def shooting_beats(beats):
    global visible_beats
    N_beats = len(beats[beats == True])

    # Settings
    max_speed = 3
    max_length = 24

    if N_beats > 0:
        # Fraction of beats that have been detected
        beat_power = float(N_beats) / dsp.N_subbands
        # Speed
        beat_speed = min(N_beats, max_speed)
        # Brightness
        beat_brightness = min(beat_power * 255.0, 255.0)
        # Length
        beat_length = int(np.sqrt(beat_power) * max_length)
        
        # Pixels
        beat_pixels = np.zeros(led.N_pixels / 2)
        beat_pixels[:beat_length] = beat_brightness
        beat_pixels = gaussian_filter1d(beat_pixels, 0.5, mode='reflect')

        # Create the beat
        beat = Beat(pixels=beat_pixels, speed=beat_speed)
        # Assign direction
        # beat.is_left = np.random.random() > 0.5
        global prev_dir
        beat.is_left = not prev_dir
        prev_dir = not prev_dir
        visible_beats = np.append(visible_beats, beat)

    # Clear pixels and add beats
    remaining_beats = []
    pixels_L = np.zeros(led.N_pixels / 2)
    pixels_R = np.zeros(led.N_pixels / 2)
    for i in range(len(visible_beats)):
        if visible_beats[i].is_left:
            pixels_L += visible_beats[i].pixels
        else:
            pixels_R += visible_beats[i].pixels
        visible_beats[i].update_pixels()
        if not visible_beats[i].finished():
            remaining_beats.append(visible_beats[i])
        
    # Enforce value limits
    pixels_L = np.clip(pixels_L, 0.0, 255.0)
    pixels_R = np.clip(pixels_R, 0.0, 255.0)
    # Only keep the beats that are still visible on the LED strip
    visible_beats = np.array(remaining_beats)
    # Update the LED values
    led.set_from_array(np.append(pixels_L[::-1], pixels_R))


def microphone_update(stream):
    data = np.fromstring(stream.read(mic.CHUNK), dtype=np.int16) / (2.0**15)
    data = np.diff(data)
    data = np.append(data, data[-1])
    
    xs, ys = dsp.fft_log_partition(data=data, subbands=dsp.N_subbands)
    beats = dsp.beat_detect(ys)
    # print('Beats:', len(beats[beats == True]))
    shooting_beats(beats)


if __name__ == "__main__":
    mic.start_stream(microphone_update)
