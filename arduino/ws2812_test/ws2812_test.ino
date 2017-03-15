#include <Arduino.h>
#include "ws2812_i2s.h"

// Set this to the number of LEDs in your LED strip
#define NUM_LEDS 250

static WS2812 ledstrip;
static Pixel_t pixels[NUM_LEDS];

void setup() {
    ledstrip.init(NUM_LEDS);
}

void loop() {
    for(int i = 0; i < NUM_LEDS; i++){
        pixels[i].R = i;
        pixels[i].B = 255 - i;
        pixels[i].G = 0;
        ledstrip.show(pixels);
        delay(50);
    }

    for(int i = 0; i < NUM_LEDS; i++){
        pixels[i].R = 0;
        pixels[i].B = 0;
        pixels[i].G = i;
        ledstrip.show(pixels);
        delay(50);
    }
}
