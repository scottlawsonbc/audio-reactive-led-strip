"""Default settings and configuration for audio reactive LED strip"""
from __future__ import print_function
from __future__ import division
import os

use_defaults = {"configuration": True,                           # See notes below for detailed explanation
                "GUI_opts": False,
                "devices": True,
                "colors": True,
                "gradients": True}

settings = {                                                      # All settings are stored in this dict

    "configuration":{  # Program configuration
                     'USE_GUI': True,                             # Whether to display the GUI
                     'DISPLAY_FPS': False,                        # Whether to print the FPS when running (can reduce performance)
                     'MIC_RATE': 48000,                           # Sampling frequency of the microphone in Hz
                     'FPS': 60,                                   # Desired refresh rate of the visualization (frames per second)
                     'MIN_FREQUENCY': 20,                         # Frequencies below this value will be removed during audio processing
                     'MAX_FREQUENCY': 18000,                      # Frequencies above this value will be removed during audio processing
                     'MAX_BRIGHTNESS': 250,                       # Frequencies above this value will be removed during audio processing
                     'N_ROLLING_HISTORY': 4,                      # Number of past audio frames to include in the rolling window
                     'MIN_VOLUME_THRESHOLD': 0.001                # No music visualization displayed if recorded audio volume below threshold
                    #'LOGARITHMIC_SCALING': True,                 # Scale frequencies logarithmically to match perceived pitch of human ear
                     },

    "GUI_opts":{"Graphs":True,                                    # Which parts of the gui to show
                "Reactive Effect Buttons":True,
                "Non Reactive Effect Buttons":True,
                "Frequency Range":True,
                "Effect Options":True},

    # All devices and their respective settings. Indexed by name, call each one what you want.
    "devices":{"Desk Strip":{
                      "configuration":{"TYPE": "ESP8266",                           # Device type (see below for all supported boards)
                                         # Required configuration for device. See below for all required keys per device
                                       "AUTO_DETECT": True,                         # Set this true if you're using windows hotspot to connect (see below for more info)
                                       "MAC_ADDR": "2c-3a-e8-2f-2c-9f",             # MAC address of the ESP8266. Only used if AUTO_DETECT is True
                                       "UDP_IP": "192.168.1.208",                   # IP address of the ESP8266. Must match IP in ws2812_controller.ino
                                       "UDP_PORT": 7778,                            # Port number used for socket communication between Python and ESP8266
                                       "MAX_BRIGHTNESS": 250,                       # Max brightness of output (0-255) (my strip sometimes bugs out with high brightness)
                                         # Other configuration 
                                       "N_PIXELS": 58,                             # Number of pixels in the LED strip (must match ESP8266 firmware)
                                       "N_FFT_BINS": 24,                            # Number of frequency bins to use when transforming audio to frequency domain
                                       "current_effect": "Energy"                   # Currently selected effect for this board, used as default when program launches
                                      },
    
                      # Configurable options for this board's effects go in this dictionary.
                      # Usage: config.settings["devices"][name]["effect_opts"][effect][option]
                      "effect_opts":{"Energy":    {"blur": 1,                       # Amount of blur to apply
                                                   "scale":0.9,                     # Width of effect on strip
                                                   "r_multiplier": 1.0,             # How much red
                                                   "g_multiplier": 1.0,             # How much green
                                                   "b_multiplier": 1.0},            # How much blue
                                     "Wave":      {"color_wave": "Red",             # Colour of moving bit
                                                   "color_flash": "White",          # Colour of flashy bit
                                                   "wipe_len":5,                    # Initial length of colour bit after beat
                                                   "decay": 0.7,                    # How quickly the flash fades away 
                                                   "wipe_speed":2},                 # Number of pixels added to colour bit every frame
                                     "Spectrum":  {"r_multiplier": 1.0,             # How much red
                                                   "g_multiplier": 1.0,             # How much green
                                                   "b_multiplier": 1.0},            # How much blue
                                     "Wavelength":{"roll_speed": 0,                 # How fast (if at all) to cycle colour overlay across strip
                                                   "color_mode": "Spectral",        # Colour gradient to display
                                                   "mirror": False,                 # Reflect output down centre of strip
                                                   "reverse_grad": False,           # Flip (LR) gradient
                                                   "reverse_roll": False,           # Reverse movement of gradient roll
                                                   "blur": 3.0,                     # Amount of blur to apply
                                                   "flip_lr":False},                # Flip output left-right
                                     "Scroll":    {"lows_color": "Red",             # Colour of low frequencies
                                                   "mids_color": "Green",             # Colour of mid frequencies
                                                   "high_color": "Blue",             # Colour of high frequencies
                                                   "decay": 0.995,                  # How quickly the colour fades away as it moves
                                                   "speed": 1,                      # Speed of scroll
                                                   "r_multiplier": 1.0,             # How much red
                                                   "g_multiplier": 1.0,             # How much green
                                                   "b_multiplier": 1.0,             # How much blue
                                                   "blur": 0.2},                    # Amount of blur to apply
                                     "Power":     {"color_mode": "Spectral",        # Colour gradient to display
                                                   "s_count": 20,                   # Initial number of sparks
                                                   "s_color": "White",              # Color of sparks
                                                   "mirror": True,                  # Mirror output down central axis
                                                   "flip_lr":False},                # Flip output left-right
                                     "Single":    {"color": "Purple"},              # Static color to show
                                     "Beat":      {"color": "Red",                  # Colour of beat flash
                                                   "decay": 0.7},                   # How quickly the flash fades away
                                     "Bars":      {"resolution":4,                  # Number of "bars"
                                                   "color_mode":"Spectral",         # Multicolour mode to use
                                                   "roll_speed":0,                  # How fast (if at all) to cycle colour colours across strip
                                                   "mirror": False,                 # Mirror down centre of strip
                                                   #"reverse_grad": False,           # Flip (LR) gradient 
                                                   "reverse_roll": False,           # Reverse movement of gradient roll
                                                   "flip_lr":False},                # Flip output left-right
                                     "Gradient":  {"color_mode":"Spectral",         # Colour gradient to display
                                                   "roll_speed": 0,                 # How fast (if at all) to cycle colour colours across strip
                                                   "mirror": False,                 # Mirror gradient down central axis
                                                   "reverse": False},               # Reverse movement of gradient
                                     "Fade":      {"color_mode":"Spectral",         # Colour gradient to fade through
                                                   "roll_speed": 1,                 # How fast (if at all) to fade through colours
                                                   "reverse": False},               # Reverse "direction" of fade (r->g->b or r<-g<-b)
                                     "Calibration":{"r": 100,
                                                    "g": 100,
                                                    "b": 100}
                                     }
                                  },
               "Main Strip":{
                     "configuration":{"TYPE": "ESP8266",                           # Device type (see below for all supported boards)
                                        # Required configuration for device. See below for all required keys per device
                                      "AUTO_DETECT": True,                         # Set this true if you're using windows hotspot to connect (see below for more info)
                                      "MAC_ADDR": "5c-cf-7f-f0-8c-f3",             # MAC address of the ESP8266. Only used if AUTO_DETECT is True
                                      "UDP_IP": "192.168.1.208",                   # IP address of the ESP8266. Must match IP in ws2812_controller.ino
                                      "UDP_PORT": 7778,                            # Port number used for socket communication between Python and ESP8266
                                      "MAX_BRIGHTNESS": 180,                       # Max brightness of output (0-255) (my strip sometimes bugs out with high brightness)
                                        # Other configuration 
                                      "N_PIXELS": 226,                             # Number of pixels in the LED strip (must match ESP8266 firmware)
                                      "N_FFT_BINS": 24,                            # Number of frequency bins to use when transforming audio to frequency domain
                                      "current_effect": "Single"                   # Currently selected effect for this board, used as default when program launches
                                     },
   
                     # Configurable options for this board's effects go in this dictionary.
                     # Usage: config.settings["devices"][name]["effect_opts"][effect][option]
                     "effect_opts":{"Energy":    {"blur": 1,                       # Amount of blur to apply
                                                  "scale":0.9,                     # Width of effect on strip
                                                  "r_multiplier": 1.0,             # How much red
                                                  "g_multiplier": 1.0,             # How much green
                                                  "b_multiplier": 1.0},            # How much blue
                                    "Wave":      {"color_wave": "Red",             # Colour of moving bit
                                                  "color_flash": "White",          # Colour of flashy bit
                                                  "wipe_len":5,                    # Initial length of colour bit after beat
                                                  "decay": 0.7,                    # How quickly the flash fades away 
                                                  "wipe_speed":2},                 # Number of pixels added to colour bit every frame
                                    "Spectrum":  {"r_multiplier": 1.0,             # How much red
                                                  "g_multiplier": 1.0,             # How much green
                                                  "b_multiplier": 1.0},            # How much blue
                                    "Wavelength":{"roll_speed": 0,                 # How fast (if at all) to cycle colour overlay across strip
                                                  "color_mode": "Spectral",        # Colour gradient to display
                                                  "mirror": False,                 # Reflect output down centre of strip
                                                  "reverse_grad": False,           # Flip (LR) gradient
                                                  "reverse_roll": False,           # Reverse movement of gradient roll
                                                  "blur": 3.0,                     # Amount of blur to apply
                                                  "flip_lr":False},                # Flip output left-right
                                    "Scroll":    {"lows_color": "Red",             # Colour of low frequencies
                                                  "mids_color": "Green",             # Colour of mid frequencies
                                                  "high_color": "Blue",             # Colour of high frequencies
                                                  "decay": 0.995,                  # How quickly the colour fades away as it moves
                                                  "speed": 1,                      # Speed of scroll
                                                  "r_multiplier": 1.0,             # How much red
                                                  "g_multiplier": 1.0,             # How much green
                                                  "b_multiplier": 1.0,             # How much blue
                                                  "blur": 0.2},                    # Amount of blur to apply
                                    "Power":     {"color_mode": "Spectral",        # Colour gradient to display
                                                  "s_count": 20,                   # Initial number of sparks
                                                  "s_color": "White",              # Color of sparks
                                                  "mirror": True,                  # Mirror output down central axis
                                                  "flip_lr":False},                # Flip output left-right
                                    "Single":    {"color": "Purple"},              # Static color to show
                                    "Beat":      {"color": "Red",                  # Colour of beat flash
                                                  "decay": 0.7},                   # How quickly the flash fades away
                                    "Bars":      {"resolution":4,                  # Number of "bars"
                                                  "color_mode":"Spectral",         # Multicolour mode to use
                                                  "roll_speed":0,                  # How fast (if at all) to cycle colour colours across strip
                                                  "mirror": False,                 # Mirror down centre of strip
                                                  #"reverse_grad": False,           # Flip (LR) gradient 
                                                  "reverse_roll": False,           # Reverse movement of gradient roll
                                                  "flip_lr":False},                # Flip output left-right
                                    "Gradient":  {"color_mode":"Spectral",         # Colour gradient to display
                                                  "roll_speed": 0,                 # How fast (if at all) to cycle colour colours across strip
                                                  "mirror": False,                 # Mirror gradient down central axis
                                                  "reverse": False},               # Reverse movement of gradient
                                    "Fade":      {"color_mode":"Spectral",         # Colour gradient to fade through
                                                  "roll_speed": 1,                 # How fast (if at all) to fade through colours
                                                  "reverse": False},               # Reverse "direction" of fade (r->g->b or r<-g<-b)
                                    "Calibration":{"r": 100,
                                                   "g": 100,
                                                   "b": 100}
                                    }
                                 }
              },



    # Collection of different colours in RGB format
    "colors":{"Red":(255,0,0),
              "Orange":(255,40,0),
              "Yellow":(255,255,0),
              "Green":(0,255,0),
              "Blue":(0,0,255),
              "Light blue":(1,247,161),
              "Purple":(80,5,252),
              "Pink":(255,0,178),
              "White":(255,255,255)},

    # Multicolour gradients. Colours must be in list above
    "gradients":{"Spectral"  : ["Red", "Orange", "Yellow", "Green", "Light blue", "Blue", "Purple", "Pink"],
                 "Dancefloor": ["Red", "Pink", "Purple", "Blue"],
                 "Sunset"    : ["Red", "Orange", "Yellow"],
                 "Ocean"     : ["Green", "Light blue", "Blue"],
                 "Jungle"    : ["Green", "Red", "Orange"],
                 "Sunny"     : ["Yellow", "Light blue", "Orange", "Blue"],
                 "Fruity"    : ["Orange", "Blue"],
                 "Peach"     : ["Orange", "Pink"],
                 "Rust"      : ["Orange", "Red"]
                 }

}


device_req_config = {"Stripless"   : None, # duh
                     "BlinkStick"  : None,
                     "DotStar"     : None,
                     "ESP8266"     : {"AUTO_DETECT": ["Auto Detect",
                                                      "Automatically detect device on network using MAC address",
                                                      "checkbox",
                                                      True],
                                      "MAC_ADDR"   : ["Mac Address",
                                                      "Hardware address of device, used for auto-detection",
                                                      "textbox",
                                                      "aa-bb-cc-dd-ee-ff"],
                                      "UDP_IP"     : ["IP Address",
                                                      "IP address of device, used if auto-detection isn't active",
                                                      "textbox",
                                                      "xxx.xxx.xxx.xxx"],
                                      "UDP_PORT"   : ["Port",
                                                      "Port used to communicate with device",
                                                      "textbox",
                                                      "7778"]},
                     "RaspberryPi" : {"LED_PIN"    : ["LED Pin",
                                                      "GPIO pin connected to the LED strip RaspberryPi (must support PWM)",
                                                      "textbox",
                                                      "10"],
                                      "LED_FREQ_HZ": ["LED Frequency",
                                                      "LED signal frequency in Hz",
                                                      "textbox",
                                                      "800000"],
                                      "LED_DMA"    : ["DMA Channel",
                                                      "DMA channel used for generating PWM signal",
                                                      "textbox",
                                                      "5"],
                                      "LED_INVERT" : ["Invert LEDs",
                                                      "Set True if using an inverting logic level converter",
                                                      "checkbox",
                                                      True]},
                     "Fadecandy"   : {"SERVER"     : ["Server Address",
                                                      "Address of Fadecandy server",
                                                      "textbox",
                                                      "localhost:7890"]}
                     }

"""
    ~~ NOTES ~~

[use_defaults]

For any dicts in this file (config.py), you can add them into the use_defaults
dict to force the program to use these values over any stored in settings.ini
that you would have set using the GUI. At runtime, settings.ini is used to update
the above dicts with custom set values. 

If you're running a headless RPi, you may want to edit settings in this file, then
specify to use the dict you wrote, rather than have the program overwrite from 
settings.ini at runtime. You could also run the program with the gui, set the 
settings that you want, then disable the gui and the custom settings will still
be loaded. Basically it works as you would expect it to.

[DEVICE TYPE]

Device used to control LED strip.

'ESP8266' means that you are using an ESP8266 module to control the LED strip
and commands will be sent to the ESP8266 over WiFi. You can have as many of 
these as your computer is able to handle.

'RaspberryPi' means that you are using a Raspberry Pi as a standalone unit to process
audio input and control the LED strip directly.

'BlinkStick' means that a BlinkstickPro is connected to this PC which will be used
to control the leds connected to it.

'Fadecandy' means that a Fadecandy server is running on your computer and is connected
via usb to a Fadecandy board connected to LEDs

'DotStar' creates an APA102-based output device. LMK if you have any success 
getting this to work becuase i have no clue if it will.

'Stripless' means that the program will run without sending data to a strip.
Useful for development etc, but doesn't look half as good ;)

[REQUIRED CONFIGURATION KEYS]

===== 'ESP8266'
 "AUTO_DETECT"            # Set this true if you're using windows hotspot to connect (see below for more info)
 "MAC_ADDR"               # MAC address of the ESP8266. Only used if AUTO_DETECT is True
 "UDP_IP"                 # IP address of the ESP8266. Must match IP in ws2812_controller.ino
 "UDP_PORT"               # Port number used for socket communication between Python and ESP8266
===== 'RaspberryPi'
 "LED_PIN"                # GPIO pin connected to the LED strip pixels (must support PWM)
 "LED_FREQ_HZ"            # LED signal frequency in Hz (usually 800kHz)
 "LED_DMA"                # DMA channel used for generating PWM signal (try 5)
 "BRIGHTNESS"             # Brightness of LED strip between 0 and 255
 "LED_INVERT"             # Set True if using an inverting logic level converter
===== 'BlinkStick'
 No required configuration keys
===== 'Fadecandy'
 "SERVER"                 # Address of Fadecandy server. (usually 'localhost:7890')
===== 'DotStar'
 No required configuration keys
===== 'Stripless'
 No required configuration keys (heh)

[AUTO_DETECT]

Set to true if the ip address of the device changes. This is the case if it's connecting
through windows hotspot, for instance. If so, give the mac address of the device. This 
allows windows to look for the device's IP using "arp -a" and finding the matching
mac address. I haven't tested this on Linux or macOS.

[FPS]

FPS indicates the desired refresh rate, or frames-per-second, of the audio
visualization. The actual refresh rate may be lower if the computer cannot keep
up with desired FPS value.

Higher framerates improve "responsiveness" and reduce the latency of the
visualization but are more computationally expensive.

Low framerates are less computationally expensive, but the visualization may
appear "sluggish" or out of sync with the audio being played if it is too low.

The FPS should not exceed the maximum refresh rate of the LED strip, which
depends on how long the LED strip is.

[N_FFT_BINS]

Fast Fourier transforms are used to transform time-domain audio data to the
frequency domain. The frequencies present in the audio signal are assigned
to their respective frequency bins. This value indicates the number of
frequency bins to use.

A small number of bins reduces the frequency resolution of the visualization
but improves amplitude resolution. The opposite is true when using a large
number of bins. More bins is not always better!

There is no point using more bins than there are pixels on the LED strip.
"""

for board in settings["devices"]:
    if settings["devices"][board]["configuration"]["TYPE"] == 'ESP8266':
        settings["devices"][board]["configuration"]["SOFTWARE_GAMMA_CORRECTION"] = False
        # Set to False because the firmware handles gamma correction + dither
    elif settings["devices"][board]["configuration"]["TYPE"] == 'RaspberryPi':
        settings["devices"][board]["configuration"]["SOFTWARE_GAMMA_CORRECTION"] = True
        # Set to True because Raspberry Pi doesn't use hardware dithering
    elif settings["devices"][board]["configuration"]["TYPE"] == 'BlinkStick':
        settings["devices"][board]["configuration"]["SOFTWARE_GAMMA_CORRECTION"] = True
    elif settings["devices"][board]["configuration"]["TYPE"] == 'DotStar':
        settings["devices"][board]["configuration"]["SOFTWARE_GAMMA_CORRECTION"] = False
    elif settings["devices"][board]["configuration"]["TYPE"] == 'Fadecandy':
        settings["devices"][board]["configuration"]["SOFTWARE_GAMMA_CORRECTION"] = False
    elif settings["devices"][board]["configuration"]["TYPE"] == 'Stripless':
        settings["devices"][board]["configuration"]["SOFTWARE_GAMMA_CORRECTION"] = False
    else:
        raise ValueError("Invalid device selected. Device {} not known.".format(settings["devices"][board]["configuration"]["TYPE"]))
    settings["devices"][board]["effect_opts"]["Power"]["s_count"] =  settings["devices"][board]["configuration"]["N_PIXELS"]//6
    # Cheeky lil fix in case the user sets an odd number of LEDs
    if settings["devices"][board]["configuration"]["N_PIXELS"] % 2:
        settings["devices"][board]["configuration"]["N_PIXELS"] -= 1

# Ignore these
# settings["configuration"]['_max_led_FPS'] = int(((settings["configuration"]["N_PIXELS"] * 30e-6) + 50e-6)**-1.0)

