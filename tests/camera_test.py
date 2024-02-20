from time import sleep
import unittest
from unittest.mock import patch, MagicMock

import cv2
from app.camera.camera import Camera
from app.config import Config


class TestCamera(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.CAMERA_INDEX = 0
        self.config.CAMERA_RESOLUTION = (640, 480)
        self.config.CAMERA_FPS = 30
        self.config.CAMERA_VFLIP = False
        self.config.CAMERA_HFLIP = False
        self.camera = Camera(self.config)

    @patch("cv2.VideoCapture")
    def test_init(self, mock_video_capture):
        mock_video_capture.return_value.isOpened.return_value = True
        camera = Camera(self.config)
        self.assertEqual(camera.nowCameraIndex, self.config.CAMERA_INDEX)
        self.assertEqual(camera.config, self.config)
        mock_video_capture.assert_called_with(0)

    @patch("cv2.VideoCapture")
    def test_change_camera(self, mock_video_capture):
        mock_video_capture.return_value.isOpened.return_value = True
        self.camera.changeCamera(1)
        self.assertEqual(self.camera.nowCameraIndex, 1)
        mock_video_capture.assert_called_with(1)

    def test_update_camera_settings(self):
        self.camera.updateCameraSettings()

    def test_set_resolution(self):
        self.camera.setResolution(800, 600)
        self.assertEqual(self.camera.config.CAMERA_RESOLUTION, (800, 600))

    def test_set_fps(self):
        self.camera.setFPS(60)
        self.assertEqual(self.camera.config.CAMERA_FPS, 60)

    def test_set_flip(self):
        self.camera.setFlip(True, True)
        self.assertEqual(self.camera.vflip, True)
        self.assertEqual(self.camera.hflip, True)
        self.assertEqual(self.camera.config.CAMERA_VFLIP, True)
        self.assertEqual(self.camera.config.CAMERA_HFLIP, True)

    @patch("cv2.VideoCapture")
    def test_get_frame(self, mock_video_capture):
        mock_video_capture.return_value.read.return_value = (True, "frame")
        ret, frame = self.camera.getFrame()
        self.assertEqual(ret, True)
        cv2.imshow("frame", frame)
        sleep(5)
        cv2.destroyAllWindows()

    @patch("cv2.VideoCapture")
    def test_close(self, mock_video_capture):
        mock_video_capture.return_value.release.return_value = True
        self.camera.close()

    @patch("cv2.VideoCapture")
    def test_start(self, mock_video_capture):
        mock_video_capture.return_value.isOpened.return_value = True
        self.camera.start()
        mock_video_capture.assert_called_with(self.camera.nowCameraIndex)

    def tearDown(self):
        self.camera.close()


if __name__ == "__main__":
    unittest.main()
