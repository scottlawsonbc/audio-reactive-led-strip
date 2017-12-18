// ws2812_dma.h 

#ifndef __WS2812_DMA_H__
#define __WS2812_DMA_H__

// type definition taken from : sdio_slv.h

typedef struct 
{
  uint32_t  blocksize:12;
  uint32_t  datalen:12;
  uint32_t  unused:5;
  uint32_t  sub_sof:1;
  uint32_t  eof:1;
  uint32_t  owner:1;
  uint32_t  buf_ptr;
  uint32_t  next_link_ptr;
} sdio_queue_t;

// -----------------------------------------------------

extern void ws2812_dma(sdio_queue_t *);

#endif

