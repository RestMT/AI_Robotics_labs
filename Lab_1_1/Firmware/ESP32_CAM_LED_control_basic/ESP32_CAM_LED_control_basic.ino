#include <WiFi.h>
#include <ESPAsyncWebServer.h>

#define RXD1 15
#define TXD1 14

char buffer[20];
int bufferIndex = 0;
bool ledState = false;

const char* ssid = "Name";
const char* password = "Password";

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

void sendToArduino(const char* msg) {
  Serial1.println(msg);
  Serial.print("Sent to Arduino -> ");
  Serial.println(msg);
}

void onWebSocketMessage(AsyncWebSocket *server, AsyncWebSocketClient *client,
                        AwsFrameInfo *info, String data) {
  data.trim();
  if (data == "on" || data == "off") {
    sendToArduino(data.c_str());
  }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
             AwsEventType type, void *arg, uint8_t *data, size_t len) {
  if (type == WS_EVT_DATA) {
    AwsFrameInfo *info = (AwsFrameInfo*)arg;
    if (info->final && info->index == 0 && info->len == len && 
info->opcode == WS_TEXT) {
      String msg = "";
      for (size_t i = 0; i < len; i++) msg += (char)data[i];
      onWebSocketMessage(server, client, info, msg);
    }
  }
}

void setup() {
  Serial.begin(115200); // Serial monitor
  Serial1.begin(9600, SERIAL_8N1, RXD1, TXD1); // UART connection to Arduino

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  ws.onEvent(onEvent);
  server.addHandler(&ws);
  server.begin();
}

void loop() {
  while (Serial1.available()) {
    char inChar = Serial1.read();
    if (inChar == '\n') {
      buffer[bufferIndex] = '\0';
      Serial.print("Received from Arduino -> ");
      Serial.println(buffer);
      bufferIndex = 0;
      break;
    } else if (bufferIndex < sizeof(buffer) - 1) {
       buffer[bufferIndex++] = inChar;
    }
  }
}
