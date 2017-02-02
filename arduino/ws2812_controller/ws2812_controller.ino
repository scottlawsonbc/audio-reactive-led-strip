#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>
// needed for library WiFiManager
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <WiFiManager.h>  //https://github.com/tzapu/WiFiManager
#include <Hash.h>
#include <WiFiUdp.h>
#include "ws2812_i2s.h"


// ***************************************************************************
// Callback for WiFiManager library when config mode is entered
// ***************************************************************************
// gets called when WiFiManager enters configuration mode
void configModeCallback(WiFiManager *myWiFiManager) {
  Serial.println("Entered config mode");
  Serial.println(WiFi.softAPIP());
  // if you used auto generated SSID, print it
  Serial.println(myWiFiManager->getConfigPortalSSID());
  // entered config mode, make led toggle faster
}

// Set to the number of LEDs in your LED strip
#define NUM_LEDS 256
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 1024
// Toggles FPS output (1 = print FPS over serial, 0 = disable output)
#define SERIAL_OUTPUT 1


// Do not change unless you know what you are doing
char magicPacket[] = "ESP8266 DISCOVERY";
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];

// LED strip
static WS2812 ledstrip;
static Pixel_t pixels[NUM_LEDS];
WiFiUDP port;


void setup() {
    // Generate a pseduo-unique hostname
    char hostname[strlen("NODEMCU")+6];
    uint16_t chipid = ESP.getChipId() & 0xFFFF;
    sprintf(hostname, "%s-%04x", "NODEMCU", chipid);


    Serial.begin(115200);
    Serial.printf("system_get_cpu_freq: %d\n", system_get_cpu_freq());

    // ***************************************************************************
    // Setup: WiFiManager
    // ***************************************************************************
    // Local intialization. Once its business is done, there is no need to keep it
    // around
    WiFiManager wifiManager;
    // reset settings - for testing
    wifiManager.resetSettings();

    // set callback that gets called when connecting to previous WiFi fails, and
    // enters Access Point mode
    wifiManager.setAPCallback(configModeCallback);

    // fetches ssid and pass and tries to connect
    // if it does not connect it starts an access point with the specified name
    // here  "AutoConnectAP"
    // and goes into a blocking loop awaiting configuration
    if (!wifiManager.autoConnect(hostname)) {
        Serial.println("failed to connect and hit timeout");
        // reset and try again, or maybe put it to deep sleep
        ESP.reset();
        delay(1000);
    }
    // if you get here you have connected to the WiFi
    Serial.println("connected...yayy :)");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    // keep LED on
    digitalWrite(BUILTIN_LED, LOW);

    port.begin(localPort);
    ledstrip.init(NUM_LEDS);
}

uint16_t N = 0;
#if SERIAL_OUTPUT
    uint32_t fpsCounter = 0;
    uint32_t secondTimer = 0;
    uint32_t frames = 0;
#endif

void loop() {

    uint16_t packetSize = port.parsePacket();

    // Prevent a crash and buffer overflow
    if (packetSize > BUFFER_LEN) {
        sendReply("ERR BUFFER OVF");
        return;
    }

    if (packetSize) {
        uint16_t len = port.read(packetBuffer, BUFFER_LEN);

        // Check for a magic packet discovery broadcast
        if (!strcmp(packetBuffer, magicPacket)) {
            char reply[50];
            sprintf(reply, "ESP8266 ACK LEDS %i", NUM_LEDS);
            sendReply(reply);
            return;
        }

        // Decode byte sequence and display on LED strip
        N = 0;
        for(uint16_t i = 0; i < len; i+=3) {
            if (N >= NUM_LEDS) {
                return;
            }
            packetBuffer[len] = 0;
            pixels[N].R = (uint8_t)packetBuffer[i+0];
            pixels[N].G = (uint8_t)packetBuffer[i+1];
            pixels[N].B = (uint8_t)packetBuffer[i+2];
            N += 1;
        }
        ledstrip.show(pixels);
        #if SERIAL_OUTPUT
        frames++;
        #endif
    }
    #if SERIAL_OUTPUT
    fpsCounter++;
    if (millis() - secondTimer >= 1000U) {
        secondTimer = millis();
        Serial.printf("FPS: %d\tREAL: %d\n", fpsCounter, frames);
        fpsCounter = 0;
        frames = 0;
    }
    #endif
}

// Sends a UDP reply packet to the sender
void sendReply(char message[]) {
    port.beginPacket(port.remoteIP(), port.remotePort());
    port.write(message);
    port.endPacket();

    #if SERIAL_OUTPUT
        Serial.println(message);
    #endif
}
