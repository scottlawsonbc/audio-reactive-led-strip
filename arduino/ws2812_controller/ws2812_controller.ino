#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>
#include <Hash.h>
#include <WiFiUdp.h>
#include <NeoPixelBus.h>    // https://github.com/Makuna/NeoPixelBus

// Set to the number of LEDs in your LED strip
#define NUM_LEDS 300
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 1024
// Toggles FPS output (1 = print FPS over serial, 0 = disable output)
#define SERIAL_OUTPUT 1
#define LED_TYPE WS2812B
#define LED_PIN 5
NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> strip(NUM_LEDS, LED_PIN);
RgbColor pixel;

// Connection settings
const char* ssid     = "YOUR SSID";
const char* password = "YOUR PASS";
IPAddress ip(192, 168, 1, 9);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

// Do not change unless you know what you are doing
char magicPacket[] = "ESP8266 DISCOVERY";
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];

// LED strip
WiFiUDP port;


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
    strip.Begin();
    strip.Show();
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
            pixel.R = (uint8_t)packetBuffer[i+0];
            pixel.G = (uint8_t)packetBuffer[i+1];
            pixel.B = (uint8_t)packetBuffer[i+2];
            strip.SetPixelColor(N, pixel);
            N += 1;
        }
        strip.Show();
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
