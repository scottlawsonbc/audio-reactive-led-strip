from __future__ import print_function
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import config
import dsp
import led
import microphone as mic


class Beat:
    def __init__(self, pixels, speed):
        self.pixels = pixels
        self.speed = float(speed)
        self.iteration = 0

    def update_pixels(self):
        self.iteration += 1

        # Roll the pixel values to the right
        # Temporal dithering is used to support fractional speed values
        roll = int(self.speed)
        roll += 1 if np.random.random() < self.speed - roll else 0
        self.pixels = np.roll(self.pixels, roll, axis=0)
        self.pixels[:roll] *= 0.0

        # Apply Gaussian blur to create a dispersion effect
        # Dispersion increases in strength over time
        sigma = (2. * .14 * self.iteration / (config.N_PIXELS * self.speed))**4.
        self.pixels = gaussian_filter1d(self.pixels, sigma, mode='constant')

        # Exponentially decay the brightness over time
        # The decay helps to direct viewer's focus to newer and brighter beats
        self.pixels *= np.exp(2. * np.log(.1) / (self.speed * config.N_PIXELS))
        self.pixels = np.round(self.pixels, decimals=2)
        self.pixels = np.clip(self.pixels, 0, 255)

    def finished(self):
        return np.array_equal(self.pixels, self.pixels * 0.0)


def rainbow(speed=1.0 / 5.0):
    # Note: assumes array is N_PIXELS / 2 long
    dt = np.pi / config.N_PIXELS
    t = time.time() * speed
    def r(t): return (np.sin(t + 0.0) + 1.0) * 1.0 / 2.0
    def g(t): return (np.sin(t + (2.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
    def b(t): return (np.sin(t + (4.0 / 3.0) * np.pi) + 1.0) * 1.0 / 2.0
    x = np.tile(0.0, (config.N_PIXELS, 3))
    for i in range(config.N_PIXELS):
        x[i][0] = r(i * dt + t)
        x[i][1] = g(i * dt + t)
        x[i][2] = b(i * dt + t)
    return x


def radiate(beats, beat_speed=1.0, max_length=26, min_beats=1):
    N_beats = len(beats[beats == True])
    # Add new beat if beats were detected
    if N_beats > 0 and N_beats >= min_beats:
        # Beat properties
        beat_power = float(N_beats) / config.N_SUBBANDS
        beat_brightness = min(beat_power * 40.0, 255.0)
        beat_brightness = max(beat_brightness, 40)
        beat_length = int(np.sqrt(beat_power) * max_length)
        beat_length = max(beat_length, 2)
        # Beat pixels
        beat_pixels = np.zeros(config.N_PIXELS / 2)
        beat_pixels[:beat_length] = beat_brightness
        # Create and add the new beat
        beat = Beat(beat_pixels, beat_speed)
        radiate.beats = np.append(radiate.beats, beat)
    # Pixels that will be displayed on the LED strip
    pixels = np.zeros(config.N_PIXELS / 2)
    if len(radiate.beats):
        pixels += sum([b.pixels for b in radiate.beats])
    for b in radiate.beats:
        b.update_pixels()
    # Only keep the beats that are still visible on the strip
    radiate.beats = [b for b in radiate.beats if not b.finished()]
    pixels = np.append(pixels[::-1], pixels)
    pixels = np.clip(pixels, 0.0, 255.0)
    pixels = (pixels * rainbow().T).T
    pixels = np.round(pixels).astype(int)
    led.pixels = pixels
    led.update()


def radiate2(beats, beat_speed=0.8, max_length=26, min_beats=1):
    N_beats = len(beats[beats == True])

    if N_beats > 0 and N_beats >= min_beats:
        index_to_color = rainbow()
        # Beat properties
        beat_power = float(N_beats) / config.N_SUBBANDS
        beat_brightness = np.round(256.0 / config.N_SUBBANDS)
        beat_brightness *= np.sqrt(config.N_SUBBANDS / N_beats)
        beat_length = int(np.sqrt(beat_power) * max_length)
        beat_length = max(beat_length, 2)
        beat_pixels = np.tile(0.0, (config.N_PIXELS / 2, 3))
        for i in range(len(beats)):
            if beats[i]:
                beat_color = np.round(index_to_color[i] * beat_brightness)
                beat_pixels[:beat_length] += beat_color
        beat_pixels = np.clip(beat_pixels, 0.0, 255.0)
        beat = Beat(beat_pixels, beat_speed)
        radiate2.beats = np.append(radiate2.beats, beat)

    # Pixels that will be displayed on the LED strip
    pixels = np.zeros((config.N_PIXELS / 2, 3))
    if len(radiate2.beats):
        pixels += sum([b.pixels for b in radiate2.beats])
    for b in radiate2.beats:
        b.update_pixels()
    radiate2.beats = [b for b in radiate2.beats if not b.finished()]
    pixels = np.append(pixels[::-1], pixels, axis=0)
    pixels = np.clip(pixels, 0.0, 255.0)
    pixels = np.round(pixels).astype(int)
    led.pixels = pixels
    led.update()


def microphone_update(stream):
    frames_per_buffer = int(config.MIC_RATE / config.FPS)
    data = np.fromstring(stream.read(frames_per_buffer), dtype=np.int16)
    data = data / 2.0**15
    xs, ys = dsp.fft_log_partition(data=data, subbands=config.N_SUBBANDS)
    beats = dsp.beat_detect(ys)
    radiate2(beats)


# Initial values for the radiate effect
radiate.beats = np.array([])
radiate2.beats = np.array([])

if __name__ == "__main__":
    mic.start_stream(microphone_update)
