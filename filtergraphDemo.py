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
import argparse
import json

N_pixels = 300
device = None

# define configs (add other configs here)
movingLightConf = 'movingLight'
movingLightsConf = 'movingLights'
spectrumConf = 'spectrum'
vu_peakConf = 'vu_peak'

deviceRasp = 'RaspberryPi'
deviceCandy = 'FadeCandy'

parser = argparse.ArgumentParser(description='Audio Reactive LED Strip')

parser.add_argument('-N', '--num_pixels',  dest='num_pixels', type=int, default=300, help = 'number of pixels (default: 300)')
parser.add_argument('-D', '--device', dest='device', default=deviceCandy, choices=[deviceRasp,deviceCandy], help = 'device to send RGB to')
parser.add_argument('--device_candy_server', dest='device_candy_server', default='127.0.0.1:7890', help = 'Server for device FadeCandy')
parser.add_argument('-C', '--config', dest='config', default=movingLightConf, choices=[movingLightConf, spectrumConf, vu_peakConf, movingLightsConf], help = 'config to use')
args = parser.parse_args()

N_pixels = args.num_pixels

if args.device == deviceRasp:
    device = devices.RaspberryPi(N_pixels)
elif args.device == deviceCandy:
    device = devices.FadeCandy(args.device_candy_server)

fg = filtergraph.FilterGraph(recordTimings=True)

audio_in = audio.AudioInput(num_channels=2)
fg.addEffectNode(audio_in)

led_out = devices.LEDOutput(device)
fg.addEffectNode(led_out)



# select config to show
config = args.config

if config == movingLightConf:
    N_pixels = int(N_pixels/2)
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)

    movingLight = effects.MovingLightEffect(N_pixels, audio_in.getSampleRate(),speed=150.0, dim_time=2.0)
    fg.addEffectNode(movingLight)

    mirrorLower = effects.MirrorEffect(N_pixels,mirror_lower=True, recursion=0)
    fg.addEffectNode(mirrorLower)

    afterglow = effects.AfterGlowEffect(N_pixels)
    fg.addEffectNode(afterglow)

    append = effects.Append(2,[1,0])
    fg.addEffectNode(append)

    fg.addConnection(audio_in,0,movingLight,0)
    fg.addConnection(color_wheel,0,movingLight,1)
    fg.addConnection(movingLight,0,afterglow,0)
    fg.addConnection(afterglow,0,append,0)
    fg.addConnection(afterglow,0,append,1)
    fg.addConnection(append,0,led_out,0)

elif config == movingLightsConf:
    N_pixels = int(N_pixels/2)
    # Layer 1
    color_wheel1 = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel1)

    movingLight1 = effects.MovingLightEffect(N_pixels, audio_in.getSampleRate(),speed=150.0, dim_time=.5,highcut_hz=200)
    fg.addEffectNode(movingLight1)

    afterglow1 = effects.AfterGlowEffect(N_pixels)
    fg.addEffectNode(afterglow1)

    append1 = effects.Append(2,[1,0])
    fg.addEffectNode(append1)

    fg.addConnection(audio_in,0,movingLight1,0)
    fg.addConnection(color_wheel1,0,movingLight1,1)
    fg.addConnection(movingLight1,0,afterglow1,0)
    fg.addConnection(afterglow1,0,append1,0)
    fg.addConnection(afterglow1,0,append1,1)
    

    # Layer 2
    color_wheel2 = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel2)

    movingLight2 = effects.MovingLightEffect(N_pixels, audio_in.getSampleRate(),speed=150.0, dim_time=1.0, highcut_hz=500)
    fg.addEffectNode(movingLight2)

    afterglow2 = effects.AfterGlowEffect(N_pixels)
    fg.addEffectNode(afterglow2)

    append2 = effects.Append(2,[0,1])
    fg.addEffectNode(append2)

    fg.addConnection(audio_in,0,movingLight2,0)
    fg.addConnection(color_wheel2,0,movingLight2,1)
    fg.addConnection(movingLight2,0,afterglow2,0)
    fg.addConnection(afterglow2,0,append2,0)
    fg.addConnection(afterglow2,0,append2,1)
    

    # Combine

    combine = effects.Combine(mode='lightenOnly')
    fg.addEffectNode(combine)
    
    fg.addConnection(append1,0,combine,0)
    fg.addConnection(append2,0,combine,1)
    fg.addConnection(combine,0,led_out,0)

elif config == spectrumConf:
    N_pixels = int(N_pixels/2)
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)

    color_wheel2 = colors.ColorWheelEffect(N_pixels, cycle_time=15.0)
    fg.addEffectNode(color_wheel2)

    spectrum = effects.SpectrumEffect(num_pixels=N_pixels, fs=audio_in.getSampleRate(), chunk_rate=60)
    fg.addEffectNode(spectrum)

    append = effects.Append(2,flipMask=[1,0])
    fg.addEffectNode(append)

    afterglow = effects.AfterGlowEffect(int(2*N_pixels), 2.0)
    fg.addEffectNode(afterglow)

    fg.addConnection(audio_in,0,spectrum,0)
    fg.addConnection(color_wheel,0,spectrum,1)
    fg.addConnection(color_wheel2,0,spectrum,2)
    fg.addConnection(spectrum,0,append,0)
    fg.addConnection(spectrum,0,append,1)
    fg.addConnection(append,0,afterglow,0)
    fg.addConnection(afterglow,0,led_out,0)

elif config == vu_peakConf:
    N_pixels = int(N_pixels/2)
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)

    color_wheel2 = colors.ColorWheelEffect(N_pixels, cycle_time=5.0)
    fg.addEffectNode(color_wheel2)

    interpCol = colors.InterpolateHSVEffect(N_pixels)
    fg.addEffectNode(interpCol)

    vu_peak = effects.VUMeterPeakEffect(N_pixels)
    fg.addEffectNode(vu_peak)

    vu_peak_R = effects.VUMeterPeakEffect(N_pixels)
    fg.addEffectNode(vu_peak_R)

    append = effects.Append(2,[0,1])
    fg.addEffectNode(append)

    afterglow = effects.AfterGlowEffect(int(2*N_pixels), 0.5)
    fg.addEffectNode(afterglow)

    fg.addConnection(audio_in,0,vu_peak,0)
    fg.addConnection(color_wheel,0,interpCol,0)
    fg.addConnection(color_wheel2,0,interpCol,1)
    fg.addConnection(interpCol,0,vu_peak,1)

    fg.addConnection(audio_in,1,vu_peak_R,0)
    fg.addConnection(interpCol,0,vu_peak_R,1)

    fg.addConnection(vu_peak,0,append,0)
    fg.addConnection(vu_peak_R,0,append,1)
    fg.addConnection(append,0,afterglow,0)
    fg.addConnection(afterglow,0,led_out,0)

else:
    raise NotImplementedError("Config not implemented")


# save filtergraph to json
filename = "configs/{}.json".format(config)
if not os.path.exists(os.path.dirname(filename)):
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

saveJson = jsonpickle.encode(fg)
temp = json.loads(saveJson)
saveJson = json.dumps(temp, sort_keys=True)

with open(filename,"w") as f:
    f.write(saveJson)

# load filtergraph from json in case there are any issues with saving/loading
#fg = jsonpickle.decode(saveJson)

current_time = timer()
count = 0
updateTiming = filtergraph.Timing()
while True:
    last_time = current_time
    current_time = timer()
    dt = current_time - last_time

    fg.update(dt)
    updateTiming.update(timer() - current_time)

    fg.process()
    if count == 100:
        fg.printProcessTimings()
        print(updateTiming.__dict__)
        count = 0
    count = count + 1
    