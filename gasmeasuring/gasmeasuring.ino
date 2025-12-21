#include <WiFiNINA.h>
#include <WiFiUdp.h>

int pingResult;

char ssid[] = "Frederiks iPhone";
char pass[] = "Cappo1234";

IPAddress localIP(172, 20, 10, 14); 
IPAddress gateway(172, 20, 10, 1); 
IPAddress subnet(255, 255, 255, 240);
IPAddress dns(8 ,8, 8, 8);

unsigned int localUdpPort = 8888;
WiFiUDP Udp;

IPAddress pcIP(172, 20, 10, 11); // PC IP
unsigned int pcPort = 9999;

int mq4 = A3;
int mq135 = A2;
const int NUM_SAMPLES = 10;

int x = 0;
int y = 0;
bool newCoordinate = false;
int mq4_sum = 0, mq135_sum = 0, sample_count = 0;
char incomingPacket[255];

void setup() {

  Serial.begin(9600);
  delay(1000);

  WiFi.config(localIP, dns, gateway, subnet); 

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

  Udp.begin(localUdpPort);
  Serial.print("Listening on UDP port ");
  Serial.println(localUdpPort);
}

// -------------------- Loop --------------------
void loop() {
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

