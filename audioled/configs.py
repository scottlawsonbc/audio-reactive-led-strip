from audioled import *

def createMovingLightGraph(N_pixels, device):
    fg = filtergraph.FilterGraph(recordTimings=True)

    audio_in = audio.AudioInput(num_channels=2)
    fg.addEffectNode(audio_in)

    led_out = devices.LEDOutput(device)
    fg.addEffectNode(led_out)
    
    N_pixels = int(N_pixels/2)
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)

    movingLight = effects.MovingLightEffect(num_pixels=N_pixels, fs=audio_in.getSampleRate())
    fg.addEffectNode(movingLight)

    mirrorLower = effects.MirrorEffect(N_pixels,mirror_lower=True, recursion=0)
    fg.addEffectNode(mirrorLower)

    afterglow = effects.AfterGlowEffect(N_pixels)
    fg.addEffectNode(afterglow)

    append = effects.Append(int(N_pixels * 2), 2,[1,0])
    fg.addEffectNode(append)

    fg.addConnection(audio_in,0,movingLight,0)
    fg.addConnection(color_wheel,0,movingLight,1)
    fg.addConnection(movingLight,0,afterglow,0)
    fg.addConnection(afterglow,0,append,0)
    fg.addConnection(afterglow,0,append,1)
    fg.addConnection(append,0,led_out,0)

    return fg

def createMovingLightsGraph(N_pixels, device):
    fg = filtergraph.FilterGraph(recordTimings=True)

    audio_in = audio.AudioInput(num_channels=2)
    fg.addEffectNode(audio_in)

    led_out = devices.LEDOutput(device)
    fg.addEffectNode(led_out)
    
    N_pixels = int(N_pixels/2)
    # Layer 1
    color_wheel1 = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel1)

    movingLight1 = effects.MovingLightEffect(N_pixels, audio_in.getSampleRate(),speed=150.0, dim_time=.5,highcut_hz=200)
    fg.addEffectNode(movingLight1)

    afterglow1 = effects.AfterGlowEffect(N_pixels)
    fg.addEffectNode(afterglow1)

    append1 = effects.Append(int(N_pixels * 2), 2,[1,0])
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

    append2 = effects.Append(int(N_pixels * 2), 2,[0,1])
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

    return fg

def createSpectrumGraph(N_pixels, device):
    fg = filtergraph.FilterGraph(recordTimings=True)

    audio_in = audio.AudioInput(num_channels=2)
    fg.addEffectNode(audio_in)

    led_out = devices.LEDOutput(device)
    fg.addEffectNode(led_out)
    

    N_pixels = int(N_pixels/2)
    color_wheel = colors.ColorWheelEffect(N_pixels)
    fg.addEffectNode(color_wheel)

    color_wheel2 = colors.ColorWheelEffect(N_pixels, cycle_time=15.0)
    fg.addEffectNode(color_wheel2)

    spectrum = effects.SpectrumEffect(num_pixels=N_pixels, fs=audio_in.getSampleRate(), chunk_rate=60)
    fg.addEffectNode(spectrum)

    append = effects.Append(int(N_pixels * 2), 2,flipMask=[1,0])
    fg.addEffectNode(append)

    afterglow = effects.AfterGlowEffect(int(2*N_pixels), glow_time=2.0)
    fg.addEffectNode(afterglow)

    fg.addConnection(audio_in,0,spectrum,0)
    fg.addConnection(color_wheel,0,spectrum,1)
    fg.addConnection(color_wheel2,0,spectrum,2)
    fg.addConnection(spectrum,0,append,0)
    fg.addConnection(spectrum,0,append,1)
    fg.addConnection(append,0,afterglow,0)
    fg.addConnection(afterglow,0,led_out,0)

    return fg


    
def createVUPeakGraph(N_pixels, device):

    fg = filtergraph.FilterGraph(recordTimings=True)

    audio_in = audio.AudioInput(num_channels=2)
    fg.addEffectNode(audio_in)

    led_out = devices.LEDOutput(device)
    fg.addEffectNode(led_out)

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

    append = effects.Append(int(N_pixels * 2), 2,[0,1])
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
    return fg