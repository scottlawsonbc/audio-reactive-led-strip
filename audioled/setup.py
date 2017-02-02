#! /usr/bin/env python
from setuptools import setup

setup(name='audioled',
      version='0.1',
      description='Audio reactive LED strip visualization',
      url='http://github.com/scottlawsonbc/audio-reactive-led-strip',
      author='Scott Lawson',
      author_email='scottlawsonbc@gmail.com',
      license='MIT',
      packages=['audioled'],
      zip_safe=False,
      include_package_data=True,
      install_requires=[
          'numpy',
          'pyaudio'
      ])
