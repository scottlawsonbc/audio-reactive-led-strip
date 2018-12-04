from audioled import opc
from audioled import devices
from audioled import audio
from audioled import effects
from audioled import colors
from audioled import filtergraph
from audioled import configs
from timeit import default_timer as timer
import numpy as np
import time
import math 
import jsonpickle
import os
import errno
import argparse
import json

num_pixels = 300
device = None
switch_time = 10 #seconds

# define configs (add other configs here)
movingLightConf = 'movingLight'
movingLightsConf = 'movingLights'
spectrumConf = 'spectrum'
vu_peakConf = 'vu_peak'
swimmingConf = 'swimming'
configChoices = [movingLightConf, spectrumConf, vu_peakConf, movingLightsConf, swimmingConf]

deviceRasp = 'RaspberryPi'
deviceCandy = 'FadeCandy'

parser = argparse.ArgumentParser(description='Audio Reactive LED Strip')

parser.add_argument('-N', '--num_pixels',  dest='num_pixels', type=int, default=300, help = 'number of pixels (default: 300)')
parser.add_argument('-D', '--device', dest='device', default=deviceCandy, choices=[deviceRasp,deviceCandy], help = 'device to send RGB to')
parser.add_argument('--device_candy_server', dest='device_candy_server', default='127.0.0.1:7890', help = 'Server for device FadeCandy')
parser.add_argument('-C', '--config', dest='config', default='', choices=configChoices, help = 'config to use, default is rolling through all configs')
parser.add_argument('-s', '--save_config', dest='save_config', type=bool, default=False, help = 'Save config to config/')
args = parser.parse_args()

num_pixels = args.num_pixels

# Initialize device
if args.device == deviceRasp:
    device = devices.RaspberryPi(num_pixels)
elif args.device == deviceCandy:
    device = devices.FadeCandy(args.device_candy_server)





# select config to show
config = args.config



def createFilterGraph(config, num_pixels, device):
    if config == movingLightConf:
        return configs.createMovingLightGraph(num_pixels, device)
    elif config == movingLightsConf:
        return configs.createMovingLightsGraph(num_pixels, device)
    elif config == spectrumConf:
        return configs.createSpectrumGraph(num_pixels, device)
    elif config == vu_peakConf:
        return configs.createVUPeakGraph(num_pixels, device)
    elif config == swimmingConf:
        return configs.createSwimmingPoolGraph(num_pixels,device)
    else:
        raise NotImplementedError("Config not implemented")

    if(args.save_config):
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
        fg = jsonpickle.decode(saveJson)
    return fg



current_time = timer()
count = 0
updateTiming = filtergraph.Timing()
config_idx = 0
last_switch_time = current_time
cur_graph = None
if args.config == '':
    cur_graph = createFilterGraph(configChoices[config_idx], num_pixels, device)
else:
    cur_graph = createFilterGraph(args.config, num_pixels, device)

while True:
    last_time = current_time
    current_time = timer()
    dt = current_time - last_time
    if args.config == '' and current_time - last_switch_time > switch_time:
        # switch configuration
        print('---switching configuration---')
        config_idx = (config_idx) % len(configChoices)
        cur_graph = createFilterGraph(configChoices[config_idx], num_pixels, device)
        config_idx = config_idx + 1
        last_switch_time = current_time

    cur_graph.update(dt)
    updateTiming.update(timer() - current_time)
    cur_graph.process()
    if count == 100:
        cur_graph.printProcessTimings()
        print(updateTiming.__dict__)
        count = 0
    count = count + 1
    