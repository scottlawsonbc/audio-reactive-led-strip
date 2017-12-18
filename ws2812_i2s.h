// ws2812_lib.h

#ifndef __WS2812_I2S_H__
#define __WS2812_I2S_H__

#include <stdint.h>
#include "ws2812_defs.h"

// include C-style header
extern "C"
{
#include "ws2812_dma.h"
};

typedef struct
{
  uint8_t G; // G,R,B order is determined by WS2812B
  uint8_t R;
  uint8_t B;
} Pixel_t;


class WS2812 
{
  public:
    WS2812(void);
    ~WS2812(void);
    void init(uint16_t num_leds);
    void show(Pixel_t *);

  private:
    uint16_t num_leds;
    uint32_t *i2s_pixels_buffer[WS2812_DITHER_NUM];
    uint32_t i2s_zeros_buffer[NUM_I2S_ZERO_WORDS]; 
    sdio_queue_t i2s_zeros_queue[WS2812_DITHER_NUM];
    sdio_queue_t i2s_pixels_queue[WS2812_DITHER_NUM];
};

#endif

// end of file
