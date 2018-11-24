from audioled import opc
from audioled import devices
from audioled import audio
from audioled import effects
from audioled import colors
from audioled import filtergraph
from timeit import default_timer as timer
import numpy as np
import time
import math 
import jsonpickle
import os
import errno


N_pixels = 300

fg = filtergraph.FilterGraph()


audio_in = audio.AudioInput()
fg.addEffectNode(audio_in)

led_out = devices.LEDOutput(devices.FadeCandy('192.168.9.241:7890'))
fg.addEffectNode(led_out)

# define configs (add other configs here)
movingLightConf = 'movingLight'
spectrumConf = 'spectrum'

# select config to show
config = movingLightConf

if config == movingLightConf:
    
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)

    movingLight = effects.MovingLightEffect(N_pixels, audio_in.getSampleRate(),speed=150.0, dim_time=2.0)
    fg.addEffectNode(movingLight)

    mirrorLower = effects.MirrorEffect(N_pixels,mirror_lower=True, recursion=0)
    fg.addEffectNode(mirrorLower)

    fg.addConnection(audio_in,0,movingLight,0)
    fg.addConnection(color_wheel,0,movingLight,1)
    fg.addConnection(movingLight,0,mirrorLower,0)
    fg.addConnection(mirrorLower,0,led_out,0)
elif config == spectrumConf:
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)
    color_wheel2 = colors.ColorWheelEffect(N_pixels, cycle_time=15.0)
    fg.addEffectNode(color_wheel2)

    spectrum = effects.SpectrumEffect(num_pixels=N_pixels, fs=audio_in.getSampleRate(), chunk_rate=60, mirror_middle=True)
    fg.addEffectNode(spectrum)

    fg.addConnection(audio_in,0,spectrum,0)
    fg.addConnection(color_wheel,0,spectrum,1)
    fg.addConnection(color_wheel2,0,spectrum,2)
    fg.addConnection(spectrum,0,led_out,0)

else:
    # other -> remove when attached to config
    vu_rms = effects.VUMeterPeakEffect(N_pixels)
    fg.addEffectNode(vu_rms)

    

    color_gen = colors.StaticColorEffect(N_pixels, 0, 255.0, 0)
    fg.addEffectNode(color_gen)

    color_wheel2 = colors.ColorWheel2_gen(N_pixels)
    fg.addEffectNode(color_wheel2)

    color_gen3 = colors.ColorDimEffect(N_pixels,cycle_time=10)
    fg.addEffectNode(color_gen3)

    interpCol = colors.InterpolateHSVEffect(N_pixels)
    fg.addEffectNode(interpCol)

    afterGlow = effects.AfterGlowEffect(N_pixels)
    fg.addEffectNode(afterGlow)

    shift = effects.ShiftEffect(N_pixels)
    fg.addEffectNode(shift)

    

    #fg.addConnection(color_gen3,0,vu_rms,1)
    #fg.addConnection(audio_in,0,vu_rms,0)
    #fg.addConnection(vu_rms,0,led_out,0)
    #fg.addConnection(color_gen,0,interpCol,1)
    #fg.addConnection(color_gen2,0,interpCol,0)
    #fg.addConnection(interpCol, 0, movingLight, 1)
    #fg.addConnection(audio_in, 0, spectrum, 0)
    #fg.addConnection(color_gen2,0,spectrum,1)
    #fg.addConnection(color_gen3,0,spectrum,2)
    fg.addConnection(audio_in,0,vu_rms,0)
    fg.addConnection(color_wheel2,0,vu_rms,1)
    #fg.addConnection(movingLight, 0, mirrorLower, 0)
    fg.addConnection(vu_rms,0,shift,0)
    fg.addConnection(shift,0,led_out,0)
    #fg.addConnection(afterGlow,0,led_out,0)


# save filtergraph to json
filename = "configs/"+config+".json"
if not os.path.exists(os.path.dirname(filename)):
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

saveJson = jsonpickle.encode(fg)
with open(filename,"w") as f:
    f.write(saveJson)

# load filtergraph from json in case there are any issues with saving/loading
fg = jsonpickle.decode(saveJson)

current_time = timer()
while True:
    last_time = current_time
    current_time = timer()
    dt = current_time - last_time

    fg.update(dt)
    fg.process()
    