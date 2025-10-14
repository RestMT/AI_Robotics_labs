import sys
import asyncio
import websockets
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget
from qasync import QEventLoop, asyncSlot

ESP32_WS_URL = "ws://192.168.31.81/ws"  # Заміни на свій


class LEDControl(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("led_control.ui", self)

        self.status_label = self.findChild(type(self.findChild(QWidget, "status_label")), "status_label")
        self.button_on = self.findChild(type(self.findChild(QWidget, "pushButton_on")), "pushButton_on")
        self.button_off = self.findChild(type(self.findChild(QWidget, "pushButton_off")), "pushButton_off")
        self.led_indicator = self.findChild(type(self.findChild(QWidget, "led_indicator")), "led_indicator")
        self.log_view = self.findChild(type(self.findChild(QWidget, "log_view")), "log_view")

        # Початковий стан лампочки — вимкнена
        self.set_led_image("off")

        self.button_on.clicked.connect(lambda: self.send_command("on"))
        self.button_off.clicked.connect(lambda: self.send_command("off"))

        self.ws = None
        self.is_running = True
        asyncio.ensure_future(self.connect_ws())

    def set_led_image(self, state):
        pixmap = QtGui.QPixmap(f"led_{state}.png")
        self.led_indicator.setPixmap(pixmap)

    def append_log(self, message):
        self.log_view.appendPlainText(message.strip())
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    async def connect_ws(self):
        while self.is_running:
            try:
                self.ws = await websockets.connect(ESP32_WS_URL)
                self.status_label.setText("Connected to ESP32")
                async for message in self.ws:
                    self.append_log(message)
            except Exception as e:
                self.status_label.setText(f"Error: {e}")
                self.ws = None
                await asyncio.sleep(1)

    @asyncSlot()
    async def send_command(self, command):
        if self.ws and self.ws.open:
            try:
                await self.ws.send(command)
                self.status_label.setText(f"LED state: {command}")
                self.set_led_image("on" if command == "on" else "off")
            except Exception as e:
                self.status_label.setText(f"Error while sending: {e}")
        else:
            self.status_label.setText("WebSocket isn’t connected")

    def closeEvent(self, event):
        self.is_running = False
        if self.ws:
            asyncio.ensure_future(self.ws.close())
        event.accept()


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = LEDControl()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
