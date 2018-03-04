#include <Arduino.h>
#include <ArduinoOTA.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#define FASTLED_ESP8266_DMA // better control for ESP8266 will output or RX pin requires fork https://github.com/coryking/FastLED
#include "FastLED.h"

/************ Network Information (CHANGE THESE FOR YOUR SETUP) ************************/
const char* ssid = "WIFI_SSID";
const char* password = "WIFI_PASSWORD";

const char* sensor_name = "TEST_SENSOR_HOSTNAME";
const char* ota_password = "OTA_PASSWORD";

const bool static_ip = true;
IPAddress ip(192, 168, 1, 112);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

const int udp_port = 7778;

/*********************************** FastLED Defintions ********************************/
#define NUM_LEDS      250
#define DATA_PIN      5
//#define CLOCK_PIN   2
#define CHIPSET       WS2812B
#define COLOR_ORDER   GRB

/*********************************** Globals *******************************************/
WiFiUDP port;
CRGB leds[NUM_LEDS];

/********************************** Start Setup ****************************************/
void setup() {
  Serial.begin(115200);

  // Setup FastLED
  #ifdef CLOCK_PIN
    FastLED.addLeds<CHIPSET, DATA_PIN, CLOCK_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  #else
    FastLED.addLeds<CHIPSET, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  #endif

  // Setup the wifi connection
  setup_wifi();

  // Setup OTA firmware updates
  setup_ota();

  // Initialize the UDP port
  port.begin(udp_port);
}

void setup_wifi() {
  delay(10);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.print(ssid);

  if (static_ip) {
    WiFi.config(ip, gateway, subnet);
  }
  
  WiFi.hostname(sensor_name);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setup_ota() {
  ArduinoOTA.setHostname(sensor_name);
  ArduinoOTA.setPassword(ota_password);

  ArduinoOTA.onStart([]() {
    Serial.println("Starting");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
  });
  ArduinoOTA.begin();
}

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    delay(1);
    Serial.print("WIFI Disconnected. Attempting reconnection.");
    setup_wifi();
    return;
  }
  
  ArduinoOTA.handle();

  // TODO: Hookup either a more elaborate protocol, or a secondary
  // communication channel (i.e. mqtt) for functional control. This
  // will also give the ability to have some non-reative effects to
  // be driven completely locally making them less glitchy.

  // Handle UDP data
  int packetSize = port.parsePacket();
  if (packetSize == sizeof(leds)) {
    port.read((char*)leds, sizeof(leds));
    FastLED.show();
  } else if (packetSize) {
    Serial.printf("Invalid packet size: %u (expected %u)\n", packetSize, sizeof(leds));
    port.flush();
    return;
  }
}