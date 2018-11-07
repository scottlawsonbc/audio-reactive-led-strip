
from audioled import opc
from audioled import devices
from audioled import audio
from audioled import effects
from audioled import colors
from timeit import default_timer as timer
import numpy as np
import time
import math 

N_pixels = 300

pixels = np.zeros((3, N_pixels))
pixels[0, 0] = 255  # Set 1st pixel red
pixels[1, 1] = 255  # Set 2nd pixel green
pixels[2, 2] = 255  # Set 3rd pixel blue
pixels[0, 3] = 255 # 4th pixel red
# Send pixels forever at 30 frames per second
device = devices.FadeCandy()
audio.print_audio_devices()
audio_stream, fs = audio.stream_audio()
chunk_rate=60
duration=1
# Instanciate effect
spectrum_effect = effects.SpectrumEffect(pixels=N_pixels, fs=fs, audio_gen=audio_stream, bass_colorgen=colors.ColorWheel_gen(), melody_colorgen=colors.ColorWheel_gen(offset=15.0), chunk_rate=chunk_rate, mirror_middle=True)
glow_effect = effects.AfterGlowEffect(num_pixels=N_pixels, pixel_gen=spectrum_effect.effect(),glow_time=.2)
# Instanciate effect
interpol  = colors.InterpolateHSV_gen(N_pixels, colors.ColorWheel_gen(), colors.ColorWheel_gen(cycle_time=15.0))
vu_effect = effects.VUMeterPeakEffect(num_pixels=N_pixels, audio_gen=audio_stream, color_gen=interpol)
glow_effect2 = effects.AfterGlowEffect(num_pixels=N_pixels, pixel_gen=vu_effect.effect(),glow_time=0.1)
shift_effect = effects.ShiftEffect(num_pixels=N_pixels, pixel_gen=glow_effect2.effect(), speed=1.0, dim_time=0.01)

# Select generator to show
gen = glow_effect.effect()

fps = 100
loop_delta = 1./fps
current_time = timer()

while True:
    last_time = current_time
    current_time = timer()
    dt = current_time - last_time
    #### processing
    spectrum_effect.update(dt)
    vu_effect.update(dt)
    glow_effect.update(dt)
    glow_effect2.update(dt)
    shift_effect.update(dt)
    pixel = next(gen)
    
    # oldnorm = float(np.linalg.norm(pixel))
    # pixels*=0.998
    # pixels+=pixel
    # newnorm = float(np.linalg.norm(pixels))
    # # print('old %d', oldnorm)
    
    # # print('new %d', newnorm)
    # if(newnorm > 0):
    #     pixels*=(oldnorm)/newnorm

    # print('now %d', float(np.linalg.norm(pixels)))
    device.show(pixel)