import numpy as np
from skimage.exposure import rescale_intensity, equalize_hist, adjust_sigmoid, equalize_adapthist

def contrast(x, gain=100.0):
    return adjust_sigmoid(x, gain=gain/10.0)

def equalize(x):
    return equalize_hist(x)