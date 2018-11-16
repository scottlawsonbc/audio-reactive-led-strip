# Audio Reactive LED Strip

[![Build Status](https://travis-ci.org/segfault16/audio-reactive-led-strip.svg?branch=develop)](https://travis-ci.org/segfault16/audio-reactive-led-strip)

Real-time LED strip music visualization using Python and the ESP8266 or Raspberry Pi.

The works in this project is based on [https://github.com/scottlawsonbc/audio-reactive-led-strip](https://github.com/scottlawsonbc/audio-reactive-led-strip).

# Getting started (local machine)

## Python Dependencies
Visualization code is compatible with Python 2.7 or 3.5. A few Python dependencies must also be installed:
- Numpy
- Scipy (for digital signal processing)
- PyAudio (for recording audio with microphone)

On Windows machines, the use of [Anaconda](https://www.continuum.io/downloads) is **highly recommended**. Anaconda simplifies the installation of Python dependencies, which is sometimes difficult on Windows.

### Installing dependencies with Anaconda
Create a [conda virtual environment](http://conda.pydata.org/docs/using/envs.html) (this step is optional but recommended)
```
conda create --name visualization-env python=3.5
source activate visualization-env
```
On Mac, you need to install portaudio
```
brew install portaudio
```

Install dependencies using pip and the conda package manager
```
conda install numpy scipy

pip install pyaudio
```

## Visualization Server

For local development we need to somehow visualize the RGB data.
For this you can use [openpixelcontrol](https://github.com/zestyping/openpixelcontrol).

- Clone the project parallel to this repository
- Follow the instructions to compile the project
- Use the compiled binary `gl_server` to start an OpenGL visualization server on port 7890 to visualize the LED strip configuration for the demo program

```
../openpixelcontrol/bin/gl_server -l layouts/demo_layout.json
```

## Running the demo

```
python demo.py
```

## Running unit tests

```
python -m unittest discover
```