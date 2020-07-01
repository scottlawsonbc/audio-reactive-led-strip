from setuptools import setup, find_packages


setup(
    name="Dancy-Pi",
    version="1.0",
    author="Nazmus Nasir",
    author_email="admin@easyprogramming.net",
    url="https://www.easyprogramming.net",
    download_url="https://github.com/naztronaut/dancyPi-audio-reactive-led",
    description="Audio Reactive Raspberry Pi with WS2812b LEDs.",
    license="MIT",
    install_requires=['numpy', 'pyaudio', 'pyqtgraph', 'scipy==1.4.1', 'rpi_ws281x']
)