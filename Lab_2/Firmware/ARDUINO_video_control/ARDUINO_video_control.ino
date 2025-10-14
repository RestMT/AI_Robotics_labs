const int ENA = 10; // PWM керування швидкістю двигуна A
const int ENB = 11; // PWM керування швидкістю двигуна B
const int IN1 = 12; // напрямок двигуна A
const int IN3 = 13; // напрямок двигуна B
const int SPEED = 255; // Швидкість

char buffer[20];
int bufferIndex = 0;

void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN3, OUTPUT);

  stopMotors();

  Serial.println("Ready to receive");
  Serial.flush();
}

void loop() {
  if (Serial.available()) {
    char inChar = Serial.read();
    if (inChar == '\n') {
      buffer[bufferIndex] = '\0';

      // Видалити \r в кінці рядка
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
    // Вперед (обидва двигуни вперед)
    digitalWrite(IN1, HIGH);
    digitalWrite(IN3, HIGH);
    analogWrite(ENA, SPEED);
    analogWrite(ENB, SPEED);
  } else if (strcmp(cmd, "s") == 0) {
    // Назад (обидва двигуни назад)
    digitalWrite(IN1, LOW);
    digitalWrite(IN3, LOW);
    analogWrite(ENA, SPEED);
    analogWrite(ENB, SPEED);
  } else if (strcmp(cmd, "a") == 0) {
    // Поворот вліво: праве колесо вперед
    digitalWrite(IN1, LOW);   // ліве колесо зупинене (або назад)
    digitalWrite(IN3, HIGH);  // праве вперед
    analogWrite(ENA, 0);
    analogWrite(ENB, SPEED);
  } else if (strcmp(cmd, "d") == 0) {
    // Поворот вправо: ліве колесо вперед
    digitalWrite(IN1, HIGH);  // ліве вперед
    digitalWrite(IN3, LOW);   // праве зупинене (або назад)
    analogWrite(ENA, SPEED);
    analogWrite(ENB, 0);
  } else if (strcmp(cmd, "halt") == 0) {
    stopMotors();
  }
}

void stopMotors() {
  digitalWrite(IN1, LOW);   // ліве колесо зупинене (або назад)
  digitalWrite(IN3, LOW);  // праве колесо зупинене (або назад)
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
