#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>
#include <Hash.h>
#include <WiFiUdp.h>
#include "ws2812_i2s.h"

// Set this to the number of LEDs in your LED strip

#define NUM_LEDS 60
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 1024
#define PRINT_FPS 1

// Wifi and socket settings
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];

// LED strip
static WS2812 ledstrip;
static Pixel_t pixels[NUM_LEDS];
WiFiUDP port;

// Network information
// IP must match the IP in config.py
IPAddress ip(192, 168, 0, 150);
// Set gateway to your router's gateway
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);

void setup() {
    Serial.begin(115200);
    WiFi.config(ip, gateway, subnet);
    WiFi.begin(ssid, password);
    Serial.println("");
    // Connect to wifi and print the IP address over serial
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.print("Connected to ");
    Serial.println(ssid);
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    port.begin(localPort);
    ledstrip.init(NUM_LEDS);
}

uint8_t N = 0;
#ifdef PRINT_FPS
    int fpsCounter = 0;
    int secondTimer = 0;
#endif

void loop() {
    // Read data over socket
    int packetSize = port.parsePacket();
    // If packets have been received, interpret the command
    if (packetSize) {
      int len = port.read(packetBuffer, BUFFER_LEN);
        for(int i = 0; i < len; i+=4){
            packetBuffer[len] = 0;
            N = packetBuffer[i];
            pixels[N].R = (uint8_t)packetBuffer[i+1];
            pixels[N].G = (uint8_t)packetBuffer[i+2];
            pixels[N].B = (uint8_t)packetBuffer[i+3];
        } 
      ledstrip.show(pixels);
      
      if(PRINT_FPS == 1)
      {
        Serial.print("*");
        fpsCounter++;
      }
  }
 if(PRINT_FPS == 1){
  if(millis() - secondTimer >= 1000)
  {
    secondTimer = millis();

    Serial.printf("FPS: %d\n", fpsCounter);
    fpsCounter = 0;
  }
 }
}
