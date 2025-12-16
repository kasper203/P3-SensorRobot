#include <WiFiNINA.h>
#include <WiFiUdp.h>

int pingResult;

// -------------------- WiFi config --------------------
char ssid[] = "Frederiks iPhone";
char pass[] = "Cappo1234";

// -------------------- Static IP config --------------------
IPAddress localIP(172, 20, 10, 14);  // static IP for Arduino
IPAddress gateway(172, 20, 10, 1);   // your router IP
IPAddress subnet(255, 255, 255, 240);
IPAddress dns(8 ,8, 8, 8);

// Local UDP port to listen for JetBot coordinates
unsigned int localUdpPort = 8888;
WiFiUDP Udp;

// PC info for sending sensor data
IPAddress pcIP(172, 20, 10, 11); // PC IP
unsigned int pcPort = 9999;

// -------------------- Sensors --------------------
int mq4 = A3;
int mq135 = A2;
const int NUM_SAMPLES = 10;

// -------------------- Variables --------------------
int x = 0;
int y = 0;
bool newCoordinate = false;
int mq4_sum = 0, mq135_sum = 0, sample_count = 0;
char incomingPacket[255];

// -------------------- Setup --------------------
void setup() {

  Serial.begin(9600);
  delay(1000);

  // Connect to WiFi with static IP
  WiFi.config(localIP, dns, gateway, subnet);  // set static IP

  Serial.print("Connecting to WiFi...");
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("Arduino IP address: ");
  Serial.println(WiFi.localIP());
  pingResult = WiFi.ping(pcIP);
  Serial.println(pingResult);

  // Start UDP listener
  Udp.begin(localUdpPort);
  Serial.print("Listening on UDP port ");
  Serial.println(localUdpPort);
  sendJSON(1,2,3,4);

}

// -------------------- Loop --------------------
void loop() {
  // 1️⃣ Receive UDP packet from JetBot
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(incomingPacket, 255);
    if (len > 0) incomingPacket[len] = 0;

    Serial.print("Received UDP: ");
    Serial.println(incomingPacket);

    String data = String(incomingPacket);
    int commaIndex = data.indexOf(',');
    if (commaIndex > 0) {
      x = data.substring(0, commaIndex).toInt();
      y = data.substring(commaIndex + 1).toInt();
      newCoordinate = true;
      mq4_sum = 0;
      mq135_sum = 0;
      sample_count = 0;
      Serial.print("New coordinate: x=");
      Serial.print(x);
      Serial.print(", y=");
      Serial.println(y);
    }
  }

  // 2️⃣ Take sensor readings
  if (newCoordinate) {
    int mq4_val = analogRead(mq4);
    int mq135_val = analogRead(mq135);

    mq4_sum += mq4_val;
    mq135_sum += mq135_val;
    sample_count++;

    delay(200);

    if (sample_count >= NUM_SAMPLES) {
      int mq4_avg = mq4_sum / NUM_SAMPLES;
      int mq135_avg = mq135_sum / NUM_SAMPLES;

      sendJSON(mq4_avg, mq135_avg, x, y);
      newCoordinate = false;
    }
  }
}

// -------------------- Send JSON over UDP --------------------
void sendJSON(int mq4, int mq135, int x, int y) {
  char json[128];
  snprintf(json, sizeof(json),
           "{ \"mq135\": %d, \"mq4\": %d, \"x\": %d, \"y\": %d }",
           mq135, mq4, x, y);

  Udp.beginPacket(pcIP, pcPort);
  Udp.write(json);
  Udp.endPacket();

  Serial.print("Sent JSON to PC: ");
  Serial.println(json);
}

