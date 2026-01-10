#include <Arduino.h>
//#include <ESP8266WiFi.h>
//#include <WiFiUdp.h>
#include <NeoPixelBus.h>

// Set to the number of LEDs in your LED strip
#define NUM_LEDS 240
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 64
// Toggles FPS output (1 = print FPS over serial, 0 = disable output)
#define PRINT_FPS 1

//NeoPixelBus settings
const uint8_t PixelPin = 7;  // make sure to set this to the correct pin, ignored for Esp8266(set to 3 by default for DMA)

char packetBuffer[BUFFER_LEN];

// LED strip
NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> ledstrip(NUM_LEDS, PixelPin);


void setup() {
    Serial.begin(115200);
    ledstrip.Begin();//Begin output
    ledstrip.Show();//Clear the strip for use
}

uint8_t N = 0;
#if PRINT_FPS
    uint16_t fpsCounter = 0;
    uint32_t secondTimer = 0;
#endif

void loop() {
    int bytes_read = 0;
    
    while(bytes_read < BUFFER_LEN) {
      if (Serial.available() > 0) {
        packetBuffer[bytes_read] = Serial.read();
        bytes_read++;
      }
    }
    bytes_read = 0;
    
    
    for (int i = 0; i < BUFFER_LEN; i+=4) {
      packetBuffer[BUFFER_LEN] = 0;
      N = packetBuffer[i];
      RgbColor pixel((uint8_t)packetBuffer[i+1], (uint8_t)packetBuffer[i+2], (uint8_t)packetBuffer[i+3]);
      ledstrip.SetPixelColor(N, pixel);  
    }

    ledstrip.Show();
}
