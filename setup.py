from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='audio_reactive_led_strip',
    version='0.0.1',
    description='Audio Reactive LED strip',
    author='scottlawsonbc',
    long_description=long_description,
    author_email='',
    #packages=find_packages(),  # same as name
    packages=['audio_reactive_led_strip'],
    package_dir={'audio_reactive_led_strip': 'python'},
    package_data={'audio_reactive_led_strip': ['*.npy']},
    # external packages as dependencies
    install_requires=['numpy', 'scipy', 'pyaudio', 'argparse'],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    entry_points = {
        'console_scripts': ['audio_reactive_led_strip=audio_reactive_led_strip.esp8266_main:main'],
    }
)
