from app.window import MainWindow,PreviewWidget
from app.config import Config
from app.camera import Camera
from PySide6.QtWidgets import QApplication
from sys import argv

if __name__ == "__main__":
    app = QApplication(argv)
    config = Config()
    camera = Camera(config)
    preview = PreviewWidget(camera)
    main = MainWindow(config, camera, preview)

    main.show()
    exit(app.exec())