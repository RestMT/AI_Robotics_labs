#include <WiFi.h>
#include <WebServer.h>
#include <ESPAsyncWebServer.h>
#include "esp_camera.h"

// ======= WiFi =======
const char* ssid = "SSID";
const char* password = "PASSWORD";

// ======= MJPEG WebServer =======
WebServer mjpegServer(80);

// ======= WebSocket Async Server =======
AsyncWebServer wsServer(81);
AsyncWebSocket ws("/ws");

// ======= UART to Arduino =======
#define RXD1 15
#define TXD1 14
char buffer[64];
int bufferIndex = 0;

// ======= Camera Config (AI Thinker) =======
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ======= Streaming control =======
volatile bool streamActive = false;
WiFiClient mjpegClient;
TaskHandle_t streamTaskHandle = NULL;

// ======= Logging =======
void sendLog(const String& msg) {
  Serial.println(msg);
  ws.textAll(msg);
}

// ======= UART Forwarding =======
void sendToArduino(const String& msg) {
  Serial1.println(msg);
  Serial1.flush();
  sendLog("Sent to Arduino -> " + msg);
}

// ======= WebSocket Callback =======
void onWebSocketMessage(AsyncWebSocket *server, AsyncWebSocketClient *client,
                        AwsFrameInfo *info, String data) {
  data.trim();

  if (data == "start") {
    streamActive = true;
    sendLog("Streaming enabled");
  } else if (data == "stop") {
    streamActive = false;
    sendLog("Streaming disabled");
  } else if (
    data == "w" || data == "a" || data == "s" || data == "d" || data == "halt"
  ) {
    sendToArduino(data);
  } else if (
    data.startsWith("pan:") || data.startsWith("tilt:")
  ) {
    // Validate and forward absolute servo commands
    int colonPos = data.indexOf(':');
    if (colonPos != -1) {
      String valuePart = data.substring(colonPos + 1);
      int angle = valuePart.toInt();
      if (angle >= 0 && angle <= 180) {
        sendToArduino(data);
      } else {
        sendLog("Invalid servo angle: " + valuePart);
      }
    }
  } else {
    sendLog("Unknown command: " + data);
  }
}

void onWsEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
               AwsEventType type, void *arg, uint8_t *data, size_t len) {
  if (type == WS_EVT_DATA) {
    AwsFrameInfo *info = (AwsFrameInfo*)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
      String msg;
      for (size_t i = 0; i < len; i++) msg += (char)data[i];
      onWebSocketMessage(server, client, info, msg);
    }
  }
}

// ======= MJPEG HTTP Handler =======
void handleVideoRequest() {
  mjpegClient = mjpegServer.client();

  mjpegClient.println("HTTP/1.1 200 OK");
  mjpegClient.println("Content-Type: multipart/x-mixed-replace; boundary=frame");
  mjpegClient.println("Connection: close");
  mjpegClient.println();

  sendLog("MJPEG client connected");

  streamActive = true;
}

// ======= MJPEG Streaming Task =======
void mjpegTask(void* pvParameters) {
  while (true) {
    if (streamActive && mjpegClient.connected()) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) continue;

      mjpegClient.print("--frame\r\n");
      mjpegClient.print("Content-Type: image/jpeg\r\n");
      mjpegClient.printf("Content-Length: %u\r\n\r\n", fb->len);
      mjpegClient.write(fb->buf, fb->len);
      mjpegClient.print("\r\n");

      esp_camera_fb_return(fb);
      delay(50);  // ~20 FPS
    } else {
      delay(100);  // Idle
    }
  }
}

// ======= Camera Init =======
bool startCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 24000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count     = 2;
  config.grab_mode    = CAMERA_GRAB_LATEST;
  config.fb_location  = CAMERA_FB_IN_PSRAM;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s != nullptr) {
    s->set_vflip(s, 1);
    s->set_hmirror(s, 1);
    pinMode(4, OUTPUT);
    digitalWrite(4, HIGH);
  }

  return true;
}

// ======= Setup =======
void setup() {
  Serial.begin(115200);
  Serial1.begin(9600, SERIAL_8N1, RXD1, TXD1);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());

  if (!startCamera()) {
    Serial.println("Camera init failed");
    while (true) delay(1000);
  }

  mjpegServer.on("/video", handleVideoRequest);
  mjpegServer.begin();
  Serial.println("MJPEG stream server started (port 80)");

  ws.onEvent(onWsEvent);
  wsServer.addHandler(&ws);
  wsServer.begin();
  Serial.println("WebSocket server started (port 81)");

  xTaskCreatePinnedToCore(mjpegTask, "mjpeg", 8192, NULL, 1, &streamTaskHandle, 1);

  sendLog("ESP32 ready");
}

// ======= Main Loop =======
void loop() {
  mjpegServer.handleClient();

  while (Serial1.available()) {
    char inChar = Serial1.read();
    if (inChar == '\n') {
      buffer[bufferIndex] = '\0';
      sendLog("Received from Arduino -> " + String(buffer));
      bufferIndex = 0;
    } else if (bufferIndex < sizeof(buffer) - 1) {
      buffer[bufferIndex++] = inChar;
    }
  }

  ws.cleanupClients();
  delay(1);
}
