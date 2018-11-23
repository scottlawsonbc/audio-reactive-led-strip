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

vu_rms = effects.VUMeterPeakEffect(N_pixels)
fg.addEffectNode(vu_rms)

movingLight = effects.MovingLightEffect(N_pixels, audio_in.getSampleRate(),speed=150.0, dim_time=2.0)
fg.addEffectNode(movingLight)

led_out = devices.LEDOutput(devices.FadeCandy('127.0.0.1:7890'))
fg.addEffectNode(led_out)

color_gen = colors.StaticColorEffect(N_pixels, 0, 255.0, 0)
fg.addEffectNode(color_gen)

color_gen2 = colors.ColorWheelEffect(N_pixels)
fg.addEffectNode(color_gen2)

color_gen3 = colors.ColorDimEffect(N_pixels,cycle_time=10)
fg.addEffectNode(color_gen3)

interpCol = colors.InterpolateHSVEffect(N_pixels)
fg.addEffectNode(interpCol)

afterGlow = effects.AfterGlowEffect(N_pixels)
fg.addEffectNode(afterGlow)

mirrorLower = effects.MirrorEffect(N_pixels,mirror_lower=False, recursion=2)
fg.addEffectNode(mirrorLower)

fg.addConnection(color_gen3,0,vu_rms,1)
fg.addConnection(audio_in,0,vu_rms,0)
fg.addConnection(vu_rms,0,led_out,0)
#fg.addConnection(color_gen,0,interpCol,1)
#fg.addConnection(color_gen2,0,interpCol,0)
#fg.addConnection(interpCol, 0, movingLight, 1)
#fg.addConnection(audio_in, 0, movingLight, 0)
#fg.addConnection(movingLight, 0, mirrorLower, 0)
#fg.addConnection(mirrorLower,0,led_out,0)
#fg.addConnection(afterGlow,0,led_out,0)

current_time = timer()
while True:
    last_time = current_time
    current_time = timer()
    dt = current_time - last_time

    fg.update(dt)
    fg.process()
    