import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from ..camera import Camera
from ..config import Config
from .previewWidget import PreviewWidget


class MainWindow(QMainWindow):
    camera: Camera = None
    config: Config = None
    perViewWidget = None

    def __init__(self, config: Config, camera: Camera,previewWidget: PreviewWidget):
        super().__init__()
        self.camera = camera
        self.config = config
        self.previewWidget = previewWidget
        self.setWindowTitle("kig-vision")
        self.showFullScreen()
        self.setCentralWidget(self.previewWidget)
        self.show()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Q:
            self.close()
        if key == Qt.Key_C:
            self.camera.nextCamera()
        if key == Qt.Key_F:
            self.camera.setFlip(not self.camera.vflip, self.camera.hflip)
        if key == Qt.Key_R:
            self.camera.updateCameraSettings()
        if key == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        if key == Qt.Key_H:
            # TODO: Add help dialog
            pass

    def closeEvent(self, event):
        self.previewWidget.timer.stop()
        self.camera.close()
        event.accept()
