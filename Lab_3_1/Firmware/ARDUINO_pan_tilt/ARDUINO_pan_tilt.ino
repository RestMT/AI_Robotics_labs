#include <Servo.h>

// Motor control pins (L298P Motor Shield)
const int ENA = 10;  // PWM speed control for motor A
const int ENB = 11;  // PWM speed control for motor B
const int IN1 = 12;  // Direction for motor A
const int IN3 = 13;  // Direction for motor B
const int SPEED = 255; // Max speed

// Servo pins
const int PAN_PIN = 9;
const int TILT_PIN = 6;
int panAngle = 90;
int tiltAngle = 90;

// Servo objects
Servo panServo;
Servo tiltServo;

// Serial buffer
char buffer[30];
int bufferIndex = 0;

void setup() {
  Serial.begin(9600);

  // Motor pins
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN3, OUTPUT);
  stopMotors();

  // Attach servos
  panServo.attach(PAN_PIN);
  tiltServo.attach(TILT_PIN);
  panServo.write(panAngle);
  tiltServo.write(tiltAngle);

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

      handleCommand(buffer);
      Serial.print(buffer);
      Serial.println();
      Serial.flush();
      bufferIndex = 0;
      
    } else if (bufferIndex < sizeof(buffer) - 1) {
      buffer[bufferIndex++] = inChar;
    }
  }
}

void handleCommand(const char* cmd) {
  if (strcmp(cmd, "w") == 0) {
    // Forward
    digitalWrite(IN1, HIGH);
    digitalWrite(IN3, HIGH);
    analogWrite(ENA, SPEED);
    analogWrite(ENB, SPEED);
  } else if (strcmp(cmd, "s") == 0) {
    // Backward
    digitalWrite(IN1, LOW);
    digitalWrite(IN3, LOW);
    analogWrite(ENA, SPEED);
    analogWrite(ENB, SPEED);
  } else if (strcmp(cmd, "a") == 0) {
    // Turn left
    digitalWrite(IN1, LOW);
    digitalWrite(IN3, HIGH);
    analogWrite(ENA, 0);
    analogWrite(ENB, SPEED);
  } else if (strcmp(cmd, "d") == 0) {
    // Turn right
    digitalWrite(IN1, HIGH);
    digitalWrite(IN3, LOW);
    analogWrite(ENA, SPEED);
    analogWrite(ENB, 0);

  } else if (strcmp(cmd, "halt") == 0) {
    stopMotors();

  } else if (strncmp(cmd, "pan:", 4) == 0) {
    // Absolute pan angle
    int val = atoi(cmd + 4);
    panAngle = constrain(val, 0, 180);
    panServo.write(panAngle);

  } else if (strncmp(cmd, "tilt:", 5) == 0) {
    // Absolute tilt angle
    int val = atoi(cmd + 5);
    tiltAngle = constrain(val, 0, 180);
    tiltServo.write(tiltAngle);
  }
}
