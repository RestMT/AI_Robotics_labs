import sys
import asyncio
import websockets
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget
from qasync import QEventLoop, asyncSlot

ESP32_WS_URL = "ws://192.168.31.81/ws"  # Заміни на свою адресу


class LEDControl(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("led_control.ui", self)

        self.status_label = self.findChild(type(self.findChild(QWidget, "status_label")), "status_label")
        self.button_on = self.findChild(type(self.findChild(QWidget, "pushButton_on")), "pushButton_on")
        self.button_off = self.findChild(type(self.findChild(QWidget, "pushButton_off")), "pushButton_off")

        self.button_on.clicked.connect(lambda: self.send_command("on"))
        self.button_off.clicked.connect(lambda: self.send_command("off"))

        self.ws = None
        self.is_running = True
        asyncio.ensure_future(self.connect_ws())

    async def connect_ws(self):
        while self.is_running:
            try:
                self.ws = await websockets.connect(ESP32_WS_URL)
                self.status_label.setText("Connected to ESP32")
                async for message in self.ws:
                    pass
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
            except Exception as e:
                self.status_label.setText(f"Error while sending: {e}")
        else:
            self.status_label.setText("WebSocket isn’t connected!")

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
