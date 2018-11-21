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

N_pixels = 300

fg = filtergraph.FilterGraph()

audio_in = audio.AudioInput()
fg.addEffectNode(audio_in)

vu_rms = effects.VUMeterRMSEffect(N_pixels)
fg.addEffectNode(vu_rms)

led_out = devices.LEDOutput(devices.FadeCandy('192.168.9.241:7890'))
fg.addEffectNode(led_out)

color_gen = colors.StaticColorEffect(N_pixels, 0, 255.0, 0)
fg.addEffectNode(color_gen)

color_gen2 = colors.ColorWheelEffect(N_pixels)
fg.addEffectNode(color_gen2)

interpCol = colors.InterpolateHSVEffect(N_pixels)
fg.addEffectNode(interpCol)

fg.addConnection(color_gen,0,interpCol,1)
fg.addConnection(color_gen2,0,interpCol,0)
fg.addConnection(interpCol, 0, vu_rms, 1)
fg.addConnection(audio_in, 0, vu_rms, 0)
fg.addConnection(vu_rms,0,led_out,0)

current_time = timer()
while True:
    last_time = current_time
    current_time = timer()
    dt = current_time - last_time

    fg.update(dt)
    fg.process()
    