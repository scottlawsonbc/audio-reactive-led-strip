# audio-reactive-led-strip
Real-time LED strip music visualization using the ESP8266 and Python

![block diagram](block-diagram.png)

![overview](description-cropped.gif)

# Demo (click gif for video)

[![visualizer demo](scroll-effect-demo.gif)](https://www.youtube.com/watch?v=HNtM7jH5GXgD)

# Overview
The repository includes everything needed to build an LED strip music visualizer (excluding hardware):

- Python real-time visualization code, which includes code for:
  - Recording audio with a microphone ([microphone.py](python/microphone.py))
  - Digital signal processing ([dsp.py](python/dsp.py))
  - Constructing 1D visualizations ([visualization.py](python/visualization.py))
  - Sending pixel information to the ESP8266 over WiFi ([led.py](python/led.py))
- Arduino firmware for the ESP8266 ([ws2812_controller.ino](arduino/ws2812_controller/ws2812_controller.ino))

# What do I need to make one?
The following hardware is needed to build an LED strip music visualizer:
- Computer with Python 2.7 or 3.5 ([Anaconda](https://www.continuum.io/downloads) is recommended on Windows)
- Any ESP8266 module with RX1 pin exposed. These modules are known to be compatible (but many others work too):
  - NodeMCU v3
  - Adafruit HUZZAH
  - Adafruit Feather HUZZAH
 - Any ws2812b LED strip (such as Adafruit Neopixels)

# Dependencies
## Python
There are only a handful of Python dependencies:
- Numpy
- Scipy (for digital signal processing)
- PyQtGraph (for GUI visualization)
- PyAudio (for recording audio with microphone)

On Windows machines, the use of [Anaconda](https://www.continuum.io/downloads) is **highly recommended**. Anaconda simplifies the installation of Python dependencies, which is sometimes difficult on Windows.

# Arduino dependencies
The [ws2812b i2s library](https://github.com/JoDaNl/esp8266_ws2812_i2s) must be downloaded and installed in the Arduino libraries folder.

