"""Settings for audio reactive LED strip"""
from __future__ import print_function
from __future__ import division
import os

N_PIXELS = 60
"""Number of pixels in the LED strip (must match ESP8266 firmware)"""

GAMMA_TABLE_PATH = os.path.join(os.path.dirname(__file__), 'gamma_table.npy')
"""Location of the gamma correction table"""

UDP_IP = '192.168.0.150'
"""IP address of the ESP8266"""

UDP_PORT = 7777
"""Port number used for socket communication between Python and ESP8266"""

#MIC_RATE = 44100
MIC_RATE = 48000
"""Sampling frequency of the microphone in Hz"""

FPS = 100
"""Desired LED strip update rate in frames (updates) per second

This is the desired update rate of the LED strip. The actual refresh rate of
the LED strip may be lower if the time needed for signal processing exceeds
the per-frame recording time.

A high FPS results in low latency and smooth animations, but it also reduces
the duration of the short-time Fourier transform. This can negatively affect
low frequency (bass) response.
"""

MIN_FREQUENCY = 200
"""Frequencies below this value will be removed during onset detection"""

MAX_FREQUENCY = 14000
"""Frequencies above this value will be removed during onset detection"""

N_SUBBANDS = 30  # 240 #48
"""Number of frequency bins to use for beat detection

More subbands improve beat detection sensitivity but it may become more
challenging for the visualization to work for a wide range of music.

Fewer subbands reduces signal processing time at the expense of beat detection
sensitivity.
"""

GAMMA_CORRECTION = True
"""Whether to correct LED brightness for nonlinear brightness perception"""

N_ROLLING_HISTORY = 2
"""Number of past audio frames to include in the rolling window"""

MIN_VOLUME_THRESHOLD = 1e-7
"""No music visualization displayed if recorded audio volume below threshold"""