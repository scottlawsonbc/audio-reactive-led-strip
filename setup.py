from setuptools import setup, find_packages


setup(
    name='AudioLED',
    version='1.0',
    description='Audio music visualization.',
    author='Scott Lawson',
    author_email='scottlawsonbc@gmail.com',
    url='https://github.com/scottlawsonbc/audio-reactive-led-strip',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=[],
    entry_points={
        'console_scripts': [
            'audioled=audioled.app:main',
            'mic=audioled.plugins.source.mic.mic:main',
            'wav=audioled.plugins.source.wav.wav:main',
            'effect=audioled.plugins.effect.standard.effect:main',
            'rgbsocket=audioled.plugins.display.socketio.server:main',
        ]
    },
    install_requires=[
        'pyaudio',
        'numpy',
        'scipy',
        'Flask',
    ]
)
