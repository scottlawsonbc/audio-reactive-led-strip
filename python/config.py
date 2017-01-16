"""Configuration module

This module is responsible for reading/writing settings to/from 
a configuration file.

To adjust settings, edit the file located in ../config/config.ini
Do not change anything in this file.

"""


import os
import configparser

parser = configparser.ConfigParser()
dirname = os.path.dirname(__file__)
"""ConfigParser for reading/writing configuration file"""
CONFIG_FILE_PATH = os.path.join(dirname, '../config/config.ini')
"""Location of the configuration file"""
GAMMA_TABLE_PATH = os.path.join(dirname, '../config/gamma_table.txt')
"""Location of the gamma correction table"""
GUI_UI_FILE_PATH = os.path.join(dirname, 'gui.ui')


def set_config_from_dict(settings_dict):
    global FPS, N_PIXELS, MIN_FREQ, MAX_FREQ, N_FFT_BINS, CMAP
    FPS = settings_dict['fps']
    N_PIXELS = settings_dict['pixels']
    # rise_val = settings_dict['rise']
    # fall_val = settings_dict['fall']
    MIN_FREQ = settings_dict['min_freq']
    MAX_FREQ = settings_dict['max_freq']
    N_FFT_BINS = settings_dict['fft_bins']
    CMAP = settings_dict['cmap']


def set_parser_from_config():
    """Set the parser values using the config module's global variables"""
    # Hardware
    parser.set('Hardware', 'device', str(DEVICE))
    parser.set('Hardware', 'pixels', str(N_PIXELS))
    parser.set('Hardware', 'sample_rate', str(MIC_RATE))
    # General
    parser.set('General', 'fps', str(FPS))
    parser.set('General', 'gui', str(USE_GUI))
    # Visualization
    parser.set('Visualization', 'freq_bins', str(N_FFT_BINS))
    parser.set('Visualization', 'min_freq', str(MIN_FREQ))
    parser.set('Visualization', 'max_freq', str(MAX_FREQ))
    parser.set('Visualization', 'cmap', str(CMAP))
    # ESP8266
    parser.set('ESP8266', 'ip', str(UDP_IP))
    parser.set('ESP8266', 'port', str(UDP_PORT))
    parser.set('ESP8266', 'gamma', str(SOFTWARE_GAMMA_CORRECTION))


def set_config_from_parser():
    """Set the config module's global variables to the parser values"""
    # Hardware
    global DEVICE, N_PIXELS, MIC_RATE
    DEVICE = parser.get('Hardware', 'device')
    N_PIXELS = parser.getint('Hardware', 'pixels')
    MIC_RATE = parser.getint('Hardware', 'sample_rate')
    # General
    global FPS, USE_GUI
    FPS = parser.getint('General', 'fps')
    USE_GUI = parser.getboolean('General', 'gui')
    # Visualization
    global N_FFT_BINS, MIN_FREQ, MAX_FREQ, MIN_VOL, CMAP
    N_FFT_BINS = parser.getint('Visualization', 'freq_bins')
    MIN_FREQ = parser.getint('Visualization', 'min_freq')
    MAX_FREQ = parser.getint('Visualization', 'max_freq')
    CMAP = parser.get('Visualization', 'cmap')
    # ESP8266
    global UDP_IP, UDP_PORT, MIN_VOLUME_THRESHOLD, SOFTWARE_GAMMA_CORRECTION
    UDP_IP = parser.get('ESP8266', 'ip')
    UDP_PORT = parser.getint('ESP8266', 'port')
    SOFTWARE_GAMMA_CORRECTION = parser.getboolean('ESP8266', 'gamma')


def read():
    """Load parser values from the config file and update global variables"""
    parser.read(CONFIG_FILE_PATH)
    set_config_from_parser()


def write():
    """Update parser values from module's globals and save to config file"""
    set_parser_from_config()
    with open(CONFIG_FILE_PATH, 'w') as configfile:
        parser.write(configfile)


# Load settings from file when this module is loaded
read()
