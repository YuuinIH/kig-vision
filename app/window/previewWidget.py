from ..camera import Camera
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer


class PreviewWidget(QWidget):
    camera: Camera = None

    def __init__(self, camera: Camera):
        super().__init__()
        self.camera = camera

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)

        self.timer.start(5)

    def update_image(self):
        ret, frame = self.camera.getFrame()
        if ret:
            image = QImage(
                frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888
            ).rgbSwapped()
            self.image_label.setPixmap(QPixmap.fromImage(image))
            self.image_label.setScaledContents(True)

    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()
        event.accept()
