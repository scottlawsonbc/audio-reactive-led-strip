from __future__ import print_function
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import dsp
import led
import microphone as mic


class Beat:
    def __init__(self, pixels, speed, direction):
        self.pixels = pixels
        self.speed = float(speed)
        self.zeros = np.zeros(len(pixels))
        self.iteration = 0
        self.direction = direction

    def update_pixels(self):
        self.iteration += 1
        self.speed = max(0.95 * self.speed, 1.0)
        self.pixels = np.roll(self.pixels, int(self.speed))
        self.pixels[:int(self.speed)] = 0.0
        s = 1.5 * self.iteration / (led.N_pixels / 2.0)
        self.pixels = gaussian_filter1d(self.pixels, s, mode='constant')
        self.pixels = np.round(self.pixels, decimals=1)

    def finished(self):
        return (self.pixels == self.zeros).all()


def radiate_effect(beats, max_speed=3, max_length=24):
    N_beats = len(beats[beats == True])
    # Add new beat if beats were detected
    if N_beats > 0:
        # Beat properties
        beat_power = float(N_beats) / dsp.N_subbands
        beat_speed = min(N_beats, max_speed)
        beat_brightness = min(beat_power * 255.0, 255.0)
        beat_length = int(np.sqrt(beat_power) * max_length)
        beat_direction = not radiate_effect.previous_direction
        # Beat pixels
        beat_pixels = np.zeros(led.N_pixels / 2)
        beat_pixels[:beat_length] = beat_brightness
        # Create and add the new beat
        beat = Beat(beat_pixels, beat_speed, beat_direction)
        radiate_effect.previous_direction = beat_direction
        radiate_effect.beats = np.append(radiate_effect.beats, beat)
    # Pixels that will be displayed on the LED strip
    pixels_L = np.zeros(led.N_pixels / 2)
    pixels_R = np.zeros(led.N_pixels / 2)
    for beat in radiate_effect.beats:
        if beat.direction:
            pixels_L += beat.pixels
        else:
            pixels_R += beat.pixels
        beat.update_pixels()
    # Only keep the beats that are still visible on the strip
    radiate_effect.beats = [b for b in radiate_effect.beats if not b.finished()]
    # Enforce value limits
    pixels_L = np.clip(pixels_L, 0.0, 255.0)
    pixels_R = np.clip(pixels_R, 0.0, 255.0)
    # Update the LED values
    led.set_from_array(np.append(pixels_L[::-1], pixels_R))


def microphone_update(stream):
    data = np.fromstring(stream.read(mic.CHUNK), dtype=np.int16) / (2.0**15)
    #data = np.diff(data)
    #data = np.append(data, data[-1])

    xs, ys = dsp.fft_log_partition(data=data, subbands=dsp.N_subbands)
    beats = dsp.beat_detect(ys)
    radiate_effect(beats)


# Settings for beat detection
dsp.ys_beat_threshold = 1.8
dsp.ys_variance_threshold = 100.0

# Initial valeus for the radiate effect
radiate_effect.previous_direction = True
radiate_effect.beats = np.array([])

if __name__ == "__main__":
    mic.start_stream(microphone_update)
