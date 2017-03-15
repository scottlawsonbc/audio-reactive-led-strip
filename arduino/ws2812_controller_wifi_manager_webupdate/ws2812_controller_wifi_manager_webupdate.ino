#include <Arduino.h>
#include <ESP8266WiFi.h>

//needed for wifimanager
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <WiFiManager.h>         //https://github.com/tzapu/WiFiManager

//needed for webUpdates
#include <ESP8266HTTPClient.h>
#include <ESP8266httpUpdate.h>

#include <WebSocketsServer.h>
#include <Hash.h>
#include <WiFiUdp.h>
#include "ws2812_i2s.h"

// Set this to the number of LEDs in your LED strip
#define NUM_LEDS 250
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 1024

// Wifi and socket settings
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];

// LED strip
static WS2812 ledstrip;
static Pixel_t pixels[NUM_LEDS];
WiFiUDP port;

void checkForUpdates()
{
        Serial.print("Checking for updates...");
        t_httpUpdate_return ret = ESPhttpUpdate.update("http://joeybabcock.me/iot/esp/updates.php");

        switch(ret) {
            case HTTP_UPDATE_FAILED:
                Serial.printf("Update Check Failed: Error (%d): %s", ESPhttpUpdate.getLastError(), ESPhttpUpdate.getLastErrorString().c_str());
                Serial.println();
                break;

            case HTTP_UPDATE_NO_UPDATES:
                Serial.println("No updates were found, continuing...");
                break;

            case HTTP_UPDATE_OK:
                Serial.println("Update Successful!");
                break;
        }
}

void setup() {
    Serial.begin(115200);
    Serial.println("");
    // Connect to wifi and print the IP address over serial
    WiFiManager wifiManager;
    //reset saved settings
    //wifiManager.resetSettings();
    wifiManager.autoConnect("EspMusicVisualizer");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    checkForUpdates();
    port.begin(localPort);
    ledstrip.init(NUM_LEDS);
    pinMode(0, OUTPUT);
}

uint8_t N = 0;
int fpsCounter = 0;
int secondTimer = 0;
int redLedTimer = 0;
void loop() {
    // Read data over socket
    int packetSize = port.parsePacket();
    // If packets have been received, interpret the command
    if (packetSize) {
      digitalWrite(0, 1);
      int len = port.read(packetBuffer, BUFFER_LEN);
        for(int i = 0; i < len; i+=4){
            packetBuffer[len] = 0;
            N = packetBuffer[i];
            pixels[N].R = (uint8_t)packetBuffer[i+1];
            pixels[N].G = (uint8_t)packetBuffer[i+2];
            pixels[N].B = (uint8_t)packetBuffer[i+3];
        } 
      ledstrip.show(pixels);
      Serial.print("*");
      fpsCounter++;
      digitalWrite(0, 0);
  }
  
  if(millis() - secondTimer >= 1000)
  {
    secondTimer = millis();

    Serial.printf("FPS: %d\n", fpsCounter);
    fpsCounter = 0;
  }
}
