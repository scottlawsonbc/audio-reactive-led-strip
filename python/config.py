"""Settings for audio reactive LED strip"""
from __future__ import print_function
from __future__ import division
import os

N_PIXELS = 240
"""Number of pixels in the LED strip (must match ESP8266 firmware)"""

GAMMA_TABLE_PATH = os.path.join(os.path.dirname(__file__), 'gamma_table.npy')
"""Location of the gamma correction table"""

UDP_IP = '192.168.1.150'
"""IP address of the ESP8266"""

UDP_PORT = 7777
"""Port number used for socket communication between Python and ESP8266"""

MIC_RATE = 44100
"""Sampling frequency of the microphone in Hz"""

FPS = 70
"""Desired LED strip update rate in frames (updates) per second

This is the desired update rate of the LED strip. The actual refresh rate of
the LED strip may be lower if the time needed for signal processing exceeds
the per-frame recording time.

A high FPS results in low latency and smooth animations, but it also reduces
the duration of the short-time Fourier transform. This can negatively affect
low frequency (bass) response.
"""


MIN_FREQUENCY = 5
"""Frequencies below this value will be removed during onset detection"""


MAX_FREQUENCY = 12000
"""Frequencies above this value will be removed during onset detection"""


ENERGY_THRESHOLD = 14.0
"""Energy threshold for determining whether a beat has been detected

One aspect of beat detection is comparing the current energy of a frequency
subband to the average energy of the subband over some time interval. Beats
are often associated with large spikes in energy relative to the recent
average energy.

ENERGY_THRESHOLD is the threshold used to determine if the energy spike is
sufficiently large to be considered a beat.

For example, if ENERGY_THRESHOLD = 2, then a beat is detected if the current
frequency subband energy is more than 2 times the recent average energy.
"""

VARIANCE_THRESHOLD = 0.0
"""Variance threshold for determining whether a beat has been detected

Beat detection is largely determined by the ENERGY_THRESHOLD, but we can also
require frequency bands to have a certain minimum variance over some past
time interval before a beat can be detected.

One downside to using a variance threshold is that it is an absolute threshold
which is affected by the current volume.
"""

N_SUBBANDS = 60  # 240 #48
"""Number of frequency bins to use for beat detection

More subbands improve beat detection sensitivity but it may become more
challenging for the visualization to work for a wide range of music.

Fewer subbands reduces signal processing time at the expense of beat detection
sensitivity.
"""

N_HISTORY = int(0.8 * FPS)
"""Number of previous samples to consider when doing beat detection

Beats are detected by comparing the most recent audio recording to a collection
of previous audio recordings. This is the number of previous audio recordings
to consider when doing beat detection.

For example, setting N_HISTORY = int(1.0 * config.FPS) means that one second
of previous audio recordings will be used for beat detection.

Smaller values reduces signal processing time but values too small may reduce
beat detection accuracy. Larger values increase signal processing time and
values too large can also reduce beat detection accuracy. Roughly one second
of previous data tends to work well.
"""

GAMMA_CORRECTION = True
"""Whether to correct LED brightness for nonlinear brightness perception"""


N_CURVES = 2
"""Number of curves to plot in the visualization window"""


N_ROLLING_HISTORY = 8
"""Number of past audio frames to include in the rolling window"""