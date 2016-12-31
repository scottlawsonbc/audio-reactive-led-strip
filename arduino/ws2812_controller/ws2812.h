// ws2812.h 

#ifndef __WS2812_H__
#define __WS2812_H__

// Gamma Correction
// Uses a nonlinear lookup table to correct for human perception of light.
// When gamma correction is used, a brightness value of 2X should appear twice
// as bright as a value of X.
// 1 = Enable gamma correction
// 0 = Disable gamma correction
// Note: There seems to be a bug and you can't actually disable this
#define WS2812_GAMMA_CORRECTION (0)

// Temporal Dithering
// Dithering preserves color and light when brightness is low.
// Sometimes this can cause undesirable flickering.
// 1 = Disable temporal dithering
// 2, 6, 8 = Enable temporal dithering (larger values = more dithering)
#define WS2812_DITHER_NUM (4)

#define WS2812_USE_INTERRUPT (0) // not supported yet

#endif

// end of file
