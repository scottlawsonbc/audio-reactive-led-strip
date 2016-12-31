// ws2812_init.c

// C-based helper function for initilalizing
// the I2S system

#include <string.h>
#include "slc_register.h"
#include "user_interface.h"
#include "ws2812_defs.h"
#include "ws2812_dma.h"


#if WS2812_USE_INTERRUPT == 1
// for debugging purposes
static volatile uint32_t interrupt_count = 0;

static void ws2812_isr(void)
{
  //clear all intr flags
  WRITE_PERI_REG(SLC_INT_CLR, 0xffffffff);//slc_intr_status);

  interrupt_count++;
}
#endif


void ws2812_dma(sdio_queue_t *i2s_pixels_queue)
{
  // Reset DMA
  SET_PERI_REG_MASK(SLC_CONF0, SLC_RXLINK_RST);    //|SLC_TXLINK_RST);
  CLEAR_PERI_REG_MASK(SLC_CONF0, SLC_RXLINK_RST);  //|SLC_TXLINK_RST);

  // Clear DMA int flags
  SET_PERI_REG_MASK(SLC_INT_CLR,  0xffffffff);
  CLEAR_PERI_REG_MASK(SLC_INT_CLR,  0xffffffff);

  // Enable and configure DMA
  CLEAR_PERI_REG_MASK(SLC_CONF0,(SLC_MODE<<SLC_MODE_S));
  SET_PERI_REG_MASK(SLC_CONF0,(1<<SLC_MODE_S));
  SET_PERI_REG_MASK(SLC_RX_DSCR_CONF,SLC_INFOR_NO_REPLACE|SLC_TOKEN_NO_REPLACE);
  CLEAR_PERI_REG_MASK(SLC_RX_DSCR_CONF, SLC_RX_FILL_EN|SLC_RX_EOF_MODE | SLC_RX_FILL_MODE);

  // configure DMA descriptor
  CLEAR_PERI_REG_MASK(SLC_RX_LINK,SLC_RXLINK_DESCADDR_MASK);
  SET_PERI_REG_MASK(SLC_RX_LINK, ((uint32)i2s_pixels_queue) & SLC_RXLINK_DESCADDR_MASK);

#if WS2812_USE_INTERRUPT == 1
  // Attach the DMA interrupt
  ets_isr_attach(ETS_SLC_INUM, (int_handler_t)ws2812_isr , (void *)0);
  
  //Enable DMA operation intr
//  WRITE_PERI_REG(SLC_INT_ENA,  SLC_RX_EOF_INT_ENA);
  //clear any interrupt flags that are set
  WRITE_PERI_REG(SLC_INT_CLR, 0xffffffff);
  ///enable DMA intr in cpu
  ets_isr_unmask(1<<ETS_SLC_INUM);
#endif

  //Start transmission
  SET_PERI_REG_MASK(SLC_RX_LINK, SLC_RXLINK_START);

  //Init pins to i2s functions
  PIN_FUNC_SELECT(PERIPHS_IO_MUX_U0RXD_U, FUNC_I2SO_DATA);

  //Enable clock to i2s subsystem
  i2c_writeReg_Mask_def(i2c_bbpll, i2c_bbpll_en_audio_clock_out, 1);

  //Reset I2S subsystem
  CLEAR_PERI_REG_MASK(I2SCONF,I2S_I2S_RESET_MASK);
  SET_PERI_REG_MASK(I2SCONF,I2S_I2S_RESET_MASK);
  CLEAR_PERI_REG_MASK(I2SCONF,I2S_I2S_RESET_MASK);

  //Select 16bits per channel (FIFO_MOD=0), no DMA access (FIFO only)
  CLEAR_PERI_REG_MASK(I2S_FIFO_CONF, I2S_I2S_DSCR_EN|(I2S_I2S_RX_FIFO_MOD<<I2S_I2S_RX_FIFO_MOD_S)|(I2S_I2S_TX_FIFO_MOD<<I2S_I2S_TX_FIFO_MOD_S));
  //Enable DMA in i2s subsystem
  SET_PERI_REG_MASK(I2S_FIFO_CONF, I2S_I2S_DSCR_EN);

  //trans master&rece slave,MSB shift,right_first,msb right
  CLEAR_PERI_REG_MASK(I2SCONF, I2S_TRANS_SLAVE_MOD|
            (I2S_BITS_MOD<<I2S_BITS_MOD_S)|
            (I2S_BCK_DIV_NUM <<I2S_BCK_DIV_NUM_S)|
            (I2S_CLKM_DIV_NUM<<I2S_CLKM_DIV_NUM_S));
  SET_PERI_REG_MASK(I2SCONF, I2S_RIGHT_FIRST|I2S_MSB_RIGHT|I2S_RECE_SLAVE_MOD|
            I2S_RECE_MSB_SHIFT|I2S_TRANS_MSB_SHIFT|
            (((WS_I2S_BCK-1)&I2S_BCK_DIV_NUM )<<I2S_BCK_DIV_NUM_S)|
            (((WS_I2S_DIV-1)&I2S_CLKM_DIV_NUM)<<I2S_CLKM_DIV_NUM_S));

#if WS2812_USE_INTERRUPT == 1
  //clear int
  SET_PERI_REG_MASK(I2SINT_CLR, I2S_I2S_RX_WFULL_INT_CLR|I2S_I2S_PUT_DATA_INT_CLR|I2S_I2S_TAKE_DATA_INT_CLR);
  CLEAR_PERI_REG_MASK(I2SINT_CLR, I2S_I2S_RX_WFULL_INT_CLR|I2S_I2S_PUT_DATA_INT_CLR|I2S_I2S_TAKE_DATA_INT_CLR);
  //enable int
  SET_PERI_REG_MASK(I2SINT_ENA,  I2S_I2S_RX_REMPTY_INT_ENA|I2S_I2S_RX_TAKE_DATA_INT_ENA);
#endif

  //Start transmission
  SET_PERI_REG_MASK(I2SCONF,I2S_I2S_TX_START);
  
}

// end of file

