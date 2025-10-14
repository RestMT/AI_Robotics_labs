import sys
import asyncio
import aiohttp
import websockets
import cv2
import numpy as np
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QWidget
from qasync import QEventLoop, asyncSlot

ESP32_WS_URL = "ws://192.168.31.81:81/ws"       # ЗАМІНІТЬ НА СВІЙ
ESP32_VIDEO_URL = "http://192.168.31.81/video"  # ЗАМІНІТЬ НА СВІЙ

ANGLE_THRESHOLD = 0.15  # Радіан ~ 8.5 градусів


class VideoControl(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("auto_control.ui", self)

        self.start_stream_button = self.findChild(QWidget, "start_stream_button")
        self.stop_stream_button = self.findChild(QWidget, "stop_stream_button")
        self.video_label = self.findChild(QWidget, "video_label")
        self.log_view = self.findChild(QWidget, "log_view")
        self.start_drive_button = self.findChild(QWidget, "start_drive_button")
        self.stop_drive_button = self.findChild(QWidget, "stop_drive_button")

        self.start_stream_button.clicked.connect(lambda: self.toggle_video(True))
        self.stop_stream_button.clicked.connect(lambda: self.toggle_video(False))
        self.start_drive_button.clicked.connect(self.start_autonomous_drive)
        self.stop_drive_button.clicked.connect(self.stop_autonomous_drive)

        self.ws = None
        self.video_task = None
        self.stream_active = False
        self.autonomous_drive = False
        self.latest_frame = None
        self.last_command = None
        asyncio.ensure_future(self.connect_ws_loop())

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
            self.append_log(f"WebSocket send error: {e}")

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
                                command, debug_frame = self.process_frame(frame)
                                if self.autonomous_drive and command and command != self.last_command:
                                    await self.send_drive_command(command)
                                    self.last_command = command

                                frame_rgb = cv2.cvtColor(debug_frame, cv2.COLOR_BGR2RGB)
                                self.latest_frame = QtGui.QImage(
                                    frame_rgb.data,
                                    frame_rgb.shape[1],
                                    frame_rgb.shape[0],
                                    frame_rgb.strides[0],
                                    QtGui.QImage.Format_RGB888
                                )
                                self.update_frame()
        except Exception as e:
            self.append_log(f"Video error: {e}")
        finally:
            self.stream_active = False
            self.video_label.setText("Stream stopped")

    def process_frame(self, frame):
        debug_frame = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 45, 80)

        height, width = edges.shape
        roi = edges[int(height/2):, :]

        lines = cv2.HoughLinesP(roi, 1, np.pi/180, 30, minLineLength=20, maxLineGap=20)
        angle_sum = 0
        count = 0

        if lines is not None:
            offset_y = int(height / 2)
            for line in lines:
                x1, y1, x2, y2 = line[0]
                y1 += offset_y
                y2 += offset_y
                cv2.line(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                angle = np.arctan2(y2 - y1, x2 - x1)
                angle_sum += angle
                count += 1

        if count == 0:
            return ("halt" if self.autonomous_drive and self.last_command != "halt" else None), debug_frame

        avg_angle = angle_sum / count

        if avg_angle > ANGLE_THRESHOLD:
            return "a", debug_frame
        elif avg_angle < -ANGLE_THRESHOLD:
            return "d", debug_frame
        else:
            return "w", debug_frame

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
        self.autonomous_drive = False
        if self.video_task:
            self.video_task.cancel()
        if self.ws:
            asyncio.ensure_future(self.ws.close())
        event.accept()

    def start_autonomous_drive(self):
        self.autonomous_drive = True
        self.last_command = None
        self.append_log("Autonomous drive started")

    def stop_autonomous_drive(self):
        self.autonomous_drive = False
        self.last_command = None
        asyncio.ensure_future(self.send_drive_command("halt"))
        self.append_log("Autonomous drive stopped")

    async def send_drive_command(self, key):
        if not self.ws or self.ws.closed:
            return
        if key in {"w", "a", "s", "d", "halt"}:
            try:
                await self.ws.send(key)
                self.append_log(f"Sent command: {key}")
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
