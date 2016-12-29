#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <DNSServer.h>
#include <WiFiManager.h>
#include <WebSocketsServer.h>
#include <Hash.h>
#include <WiFiUdp.h>
#include <ws2812_i2s.h>

// Set this to the number of LEDs in your LED strip
#define NUM_LEDS 300
#define BUFFER_LEN 1024

// Wifi and socket settings
const char* ssid     = "Bjoeandy_5ghz";
const char* password = "02030410";
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];

// LED strip
static WS2812 ledstrip;
static Pixel_t pixels[NUM_LEDS];
WiFiUDP port;

// Network information
// IP must match the IP in config.py
IPAddress ip(192, 168, 1, 2);

void setup() {
    Serial.begin(115200);
    WiFiManager wifiManager;

    wifiManager.autoConnect();
    Serial.println("");
    Serial.print("Connected to ");
    Serial.println(ssid);
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
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
