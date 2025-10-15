
# 🤖 AI Robotics Labs

Цей репозиторій містить серію лабораторних робіт з дисципліни **"Робототехніка та Інтелектуальні системи"**, виконаних на основі Python, ESP32-CAM та Arduino.  
Мета проєкту — дослідження методів комп’ютерного зору, керування роботами з ПК через по Wi-Fi, та інтеграція програмних рішень з моделями штучного інтелекту.

---

## 📂 Структура репозиторію

```
AI_Robotics_labs/
├── requirements.txt                # Залежності Python-проєктів
│
├── ESP32-CAM libraries/            # Бібліотеки для ESP32-CAM (Arduino IDE)
│   ├── AsyncTCP-main.zip
│   └── ESPAsyncWebServer-main.zip
│
├── Lab_1_1/                        # Лабораторна 1.1
│   ├── GUI_LED_control_basic.py
│   ├── GUI_LED_control_with_logs.py
│   ├── led_control.ui
│   ├── led_on.png / led_off.png
│   └── Firmware/                   # Arduino / ESP32 прошивки
│       ├── ARDUINO_LED_control_basic/
│       ├── ESP32_CAM_LED_control_basic/
│       └── ESP32_CAM_LED_control_with_logs/
│
├── Lab_1_2/                        # Лабораторна 1.2
│   ├── GUI_video_control.py
│   └── Firmware/
│       ├── ARDUINO_video_control/
│       └── ESP32_CAM_video_control/
│
├── Lab_2/                          # Лабораторна 2
│   ├── GUI_line_tracking.py
│   └── Firmware/
│       ├── ARDUINO_video_control/
│       └── ESP32_CAM_video_control/
│
├── Lab_3_1/                        # Лабораторна 3.1
│   ├── GUI_pan_tilt.py
│   └── Firmware/
│       ├── ARDUINO_pan_tilt/
│       └── ESP32_CAM_pan_tilt/
│
└── Lab_3_2/                        # Лабораторна 3.2
│    ├── yolov8n.pt
│    ├── GUI_YOLO_detection.py
│    ├── GUI_YOLO_tracking.py
│	 └── Firmware/
│       ├── ARDUINO_pan_tilt/
│       └── ESP32_CAM_pan_tilt/

```

---

## ⚙️ Встановлення середовища

1. **Клонувати репозиторій:**
   ```bash
   git clone https://github.com/RestMT/AI_Robotics_labs.git
   cd AI_Robotics_labs
   ```

2. **Встановити залежності:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Опис лабораторних робіт

### 🔹 Lab 1.1 — Створення графічного інтерфейсу для дистанційного керування мікроконтролером
- Простий інтерфейс **PyQt5** для надсилання команд on/off на Arduino за ПК через Wi-Fi ESP32-CAM.
- Передача команд відбувається через **WebSocket**.
- Візуальне відображення стану світлодіода в GUI на ПК.

### 🔹 Lab 1.2 — Дистанційне керування роботом
- Керування запуском і зупинкою **MJPEG-сервера** на ESP32-CAM.
- Відображення відеопотоку в GUI.
- Дистанційне керування роботом з клавіатури ПК.

### 🔹 Lab 2 — Алгоритм автономної навігації робота (Line Tracking)
- Обробка відеопотоку засобами **OpenCV** для виявлення ліній.
- Генерація команд керування роботом на основі аналізу відео для його руху в межах ліній.

### 🔹 Lab 3.1 — Керування роботизованим маніпулятором на прикладі механізму Pan-Tilt
- Керування двома **сервоприводами (pan, tilt)** з Python GUI.
- Механізм Pan-Tilt дозволяє направляти камеру на різні об'єкти.

### 🔹 Lab 3.2 — Автоматичне детектування та відстеження об’єктів мобільним роботом
- Інтеграція моделі **yolov8n.pt** для розпізнавання об'єктів.
- Автоматичне наведення камери на об’єкт заданого класу.
- Підтримка режимів детектування та відслідковування об'єктів.

---

## 🧩 Бібліотеки ESP32-CAM

Папка `ESP32-CAM libraries` містить архіви:
- `AsyncTCP-main.zip`
- `ESPAsyncWebServer-main.zip`

Їх потрібно встановити в Arduino IDE через:
```
Sketch → Include Library → Add .ZIP Library...
```

---


📅 *Останнє оновлення:* 14.10.2025
