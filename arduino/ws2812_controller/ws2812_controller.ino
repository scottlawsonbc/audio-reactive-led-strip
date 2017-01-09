#include <Arduino.h>
#include <ESP8266WiFi.h>

//needed for wifimanager
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <WiFiManager.h>

//needed for visualizer part
#include <WebSocketsServer.h>
#include <Hash.h>
#include <WiFiUdp.h>

//custom driver for ws2812's
#include "ws2812_i2s.h"

// Set to the number of LEDs in your LED strip
#define NUM_LEDS 60
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 1024
// Toggles FPS output (1 = print FPS over serial, 0 = disable output)
#define PRINT_FPS 1

// Wifi and socket settings
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];
String lastCmd;

void handleFps();
void handleCmd();

// LED strip
static WS2812 ledstrip;
static Pixel_t pixels[NUM_LEDS];
WiFiUDP port;
ESP8266WebServer server (localPort+1);

void setup() {
    Serial.begin(115200);
    Serial.println("Setup");
    // Connect to wifi and print the IP address over serial
    WiFiManager wifiManager;
    //wifiManager.resetSettings();
    wifiManager.autoConnect("EspMusicVisualizer");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    port.begin(localPort);
    ledstrip.init(NUM_LEDS);
    pinMode(0, OUTPUT);
    server.begin();
    server.on("/fps", handleCmd);
    server.on("/", handleCmd);
}

uint8_t N = 0;
#if PRINT_FPS
    uint16_t fpsCounter = 0;
    uint32_t secondTimer = 0;
#endif
int lastCount = 0;

void parseUdpInput()
{
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
      #if PRINT_FPS
            fpsCounter++;
            Serial.print("*");
      #endif
  }
  #if PRINT_FPS
        if (millis() - secondTimer >= 1000U) {
            secondTimer = millis();
            Serial.printf("FPS: %d\n", fpsCounter);
            fpsCounter = 0;
        }   
   #endif
}

void loop() {
    parseUdpInput();
    yield();
    server.handleClient();
}

void handleResponse(String cmd = "Works!") {
      server.send(200, "text/html", cmd);
      //Serial.println("Client succesfully executed "+cmd);
}

String handleInput(String cmd)
{
  if(cmd == "fps")                   //returns fps as a raw number
  {
    return String(lastCount);
  } else if(cmd == "responseEnabled")//returns 8266 if this ip works with visualizer
  {
    return "8266";
  } else if(cmd == "restart")        //restarts the controller
  {
    ESP.restart();
    return "1";
  }
  else {
    return "You asked for nothing. That is what you will get.";
  }
}

void handleCmd(){
  for (uint8_t i=0; i<server.args(); i++){
    if(server.argName(i) == "cmd") 
    {
      lastCmd = handleInput(server.arg(i));
      //Serial.println("@"+server.arg(i));
    }
  }
  handleResponse(lastCmd);
}
