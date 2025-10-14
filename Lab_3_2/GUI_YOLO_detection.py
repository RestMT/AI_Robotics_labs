import sys
import asyncio
import aiohttp
import websockets
import cv2
import numpy as np
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QWidget
from qasync import QEventLoop, asyncSlot
from ultralytics import YOLO

ESP32_WS_URL = "ws://192.168.31.81:81/ws"       # ЗАМІНІТЬ НА СВІЙ
ESP32_VIDEO_URL = "http://192.168.31.81/video"  # ЗАМІНІТЬ НА СВІЙ

KEY_COMMANDS = {
    QtCore.Qt.Key_W: 'w',
    QtCore.Qt.Key_A: 'a',
    QtCore.Qt.Key_S: 's',
    QtCore.Qt.Key_D: 'd',
}


class VideoControl(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("pan-tilt_autocontrol.ui", self)

        # Load YOLOv8 nano model (PyTorch format)
        self.yolo_model = YOLO("yolov8n.pt")

        # Video + log
        self.start_stream_button = self.findChild(QWidget, "start_stream_button")
        self.stop_stream_button = self.findChild(QWidget, "stop_stream_button")
        self.video_label = self.findChild(QWidget, "video_label")
        self.log_view = self.findChild(QWidget, "log_view")

        # Button callbacks
        self.start_stream_button.clicked.connect(lambda: self.toggle_video(True))
        self.stop_stream_button.clicked.connect(lambda: self.toggle_video(False))

        self.ws = None
        self.video_task = None
        self.stream_active = False
        self.latest_frame = None
        self.pressed_keys = set()

        asyncio.ensure_future(self.connect_ws_loop())
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def append_log(self, msg):
        self.log_view.appendPlainText(f"[{QtCore.QTime.currentTime().toString()}] {msg}")

    async def connect_ws_loop(self):
        while True:
            if self.ws is None or self.ws.closed:
                try:
                    self.ws = await websockets.connect(ESP32_WS_URL)
                    self.append_log("Connected to WebSocket")
                    asyncio.ensure_future(self.receive_ws())
                except Exception as e:
                    self.append_log(f"WebSocket error: {e}")
            await asyncio.sleep(0.5)

    async def receive_ws(self):
        try:
            async for message in self.ws:
                self.append_log(f"ESP32: {message}")
        except Exception as e:
            self.append_log(f"WebSocket lost: {e}")
            self.ws = None

    @asyncSlot()
    async def toggle_video(self, enable):
        if not self.ws or self.ws.closed:
            self.append_log("WebSocket not connected")
            return
        try:
            await self.ws.send("start" if enable else "stop")
            self.stream_active = enable
            if enable:
                if self.video_task:
                    self.video_task.cancel()
                self.video_task = asyncio.ensure_future(self.video_stream_task())
            else:
                if self.video_task:
                    self.video_task.cancel()
                self.video_label.clear()
                self.latest_frame = None
        except Exception as e:
            self.append_log(f"WebSocket error: {e}")

    async def video_stream_task(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ESP32_VIDEO_URL) as resp:
                    if resp.status != 200:
                        self.append_log(f"HTTP error: {resp.status}")
                        return

                    buffer = b""
                    while self.stream_active:
                        chunk = await resp.content.read(4096)
                        if not chunk:
                            break
                        buffer += chunk

                        start = buffer.find(b'\xff\xd8')
                        end = buffer.find(b'\xff\xd9', start)
                        if start != -1 and end != -1:
                            jpeg = buffer[start:end + 2]
                            buffer = buffer[end + 2:]

                            img_np = np.frombuffer(jpeg, np.uint8)
                            frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                            if frame is not None:
                                # Perform detection
                                frame = self.process_yolo(frame)
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                self.latest_frame = QtGui.QImage(
                                    frame.data,
                                    frame.shape[1],
                                    frame.shape[0],
                                    frame.strides[0],
                                    QtGui.QImage.Format_RGB888
                                )
                                self.update_frame()
        except Exception as e:
            self.append_log(f" Video error: {e}")
        finally:
            self.stream_active = False
            self.video_label.setText("Stream stopped")

    def process_yolo(self, frame):
        # Run YOLO detection (input size automatically handled)
        results = self.yolo_model(frame, imgsz=320, conf=0.5)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = f"{self.yolo_model.names[cls]} {conf:.2f}"

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame

    def update_frame(self):
        if self.latest_frame and not self.latest_frame.isNull():
            pix = QtGui.QPixmap.fromImage(self.latest_frame).scaled(
                self.video_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            self.video_label.setPixmap(pix)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.latest_frame is not None:
            QtCore.QTimer.singleShot(30, self.update_frame)

    def closeEvent(self, event):
        self.stream_active = False
        if self.video_task:
            self.video_task.cancel()
        if self.ws:
            asyncio.ensure_future(self.ws.close())
        event.accept()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key in KEY_COMMANDS and key not in self.pressed_keys:
            self.pressed_keys.add(key)
            asyncio.ensure_future(self.send_drive_command(KEY_COMMANDS[key]))

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
            if not self.pressed_keys:
                asyncio.ensure_future(self.send_drive_command("halt"))

    async def send_drive_command(self, key):
        if not self.ws or self.ws.closed:
            return
        try:
            await self.ws.send(key)
            self.append_log(f"Command sent: {key}")
        except Exception as e:
            self.append_log(f"Send error: {e}")


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = VideoControl()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
