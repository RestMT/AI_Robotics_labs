char buffer[20];
int bufferIndex = 0;

void setup() {
  Serial.begin(9600); // UART and monitor
  pinMode(LED_BUILTIN, OUTPUT); // Built-in LED
  Serial.println("Ready to receive");
  Serial.flush();
}

void loop() {
  if (Serial.available()) {
    char inChar = Serial.read();
    if (inChar == '\n') {
      buffer[bufferIndex] = '\0';

        // Remove trailing \r if present
      if (bufferIndex > 0 && buffer[bufferIndex - 1] == '\r') {
      buffer[--bufferIndex] = '\0';
      }

      // Handle command
      if (strcmp(buffer, "on") == 0) {
        digitalWrite(LED_BUILTIN, HIGH);
      } else if (strcmp(buffer, "off") == 0) {
        digitalWrite(LED_BUILTIN, LOW);
      }

      // Send confirmation back
      Serial.print(buffer);
      Serial.println();
      Serial.flush();
      bufferIndex = 0;
    } else if (bufferIndex < sizeof(buffer) - 1) {
      buffer[bufferIndex++] = inChar;
    }
  }
}
