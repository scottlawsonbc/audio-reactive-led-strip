#!/usr/bin/env python3

import time
from rpi_ws281x import *
import argparse
import config

# LED strip configuration:
LED_COUNT = config.N_PIXELS # Number of LED pixels.
LED_PIN = config.LED_PIN  # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = config.LED_FREQ_HZ   # LED signal frequency in hertz (usually 800khz)
LED_DMA = config.LED_DMA  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = config.BRIGHTNESS  # Set to 0 for darkest and 255 for brightest
LED_INVERT = config.LED_INVERT  # True to invert the signal (when using NPN transistor level shift)

# not in config
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53


# Define functions which animate LEDs in various ways.
def color_wipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


# Main program logic follows:
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    color_wipe(strip, Color(0, 0, 0), 10)
