// ws2812.h 

#ifndef __WS2812_H__
#define __WS2812_H__

// Temporal Dithering
// Dithering preserves color and light when brightness is low.
// Sometimes this can cause undesirable flickering.
// 1 = Disable temporal dithering
// 2, 6, 8 = Enable temporal dithering (larger values = more dithering)
#define WS2812_DITHER_NUM (8)

#define WS2812_USE_INTERRUPT (0) // not supported yet

#endif

// end of file
