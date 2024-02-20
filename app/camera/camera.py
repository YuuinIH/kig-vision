import logging
import cv2
from ..config import Config

class Camera:
    availableCameras = []
    nowCameraIndex = 0
    camera = None
    config = None
    vflip = False
    hflip = False

    def __init__(self,config:Config):
        self.availableCameras = self.getAvailableCameras()
        if len(self.availableCameras) == 0:
            logging.error("No cameras found")
            raise Exception("No cameras found")
        self.camera = cv2.VideoCapture(self.availableCameras[0])
        self.camera.set(cv2.CV_CAP_PROP_FOURCC,cv2.VideoWriter.fourcc('M','J','P','G'))
        self.config = config
        self.nowCameraIndex = config.CAMERA_INDEX
        self.updateCameraSettings()
        self.setFlip(config.CAMERA_VFLIP, config.CAMERA_HFLIP)
        logging.info(f"Camera {self.nowCameraIndex} initialized")

    def getAvailableCameras(self):
        cameras = []
        for i in range(Config.CAMERA_SEARCH_LIMIT):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(i)
                cap.release()
        logging.info(f"Available cameras: {cameras}")
        return cameras
    
    def changeCamera(self, cameraIndex):
        self.camera.release()
        self.camera = cv2.VideoCapture(self.availableCameras[cameraIndex])
        self.nowCameraIndex = cameraIndex
        self.config.CAMERA_INDEX = cameraIndex
        self.config.save()
        logging.info(f"Changed camera to {cameraIndex}")
        self.updateCameraSettings()

    def nextCamera(self):
        if self.nowCameraIndex + 1 < len(self.availableCameras):
            self.changeCamera(self.nowCameraIndex + 1)
        else:
            self.changeCamera(0)
        logging.info(f"Next camera: {self.nowCameraIndex}")

    def updateCameraSettings(self):
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_RESOLUTION[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_RESOLUTION[1])
        self.camera.set(cv2.CAP_PROP_FPS, self.config.CAMERA_FPS)
        logging.info(f"Updated camera settings: {self.config.CAMERA_RESOLUTION} {self.config.CAMERA_FPS}")

    def setResolution(self, width, height):
        self.config.CAMERA_RESOLUTION = (width, height)
        self.config.save()
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        logging.info(f"Changed camera resolution to {width}x{height}")

    def setFPS(self, fps):
        self.config.CAMERA_FPS = fps
        self.config.save()
        self.camera.set(cv2.CAP_PROP_FPS, fps)
        logging.info(f"Changed camera fps to {fps}")

    def setFlip(self, vflip=False, hflip=False):
        self.vflip = vflip
        self.hflip = hflip
        self.config.CAMERA_VFLIP = vflip
        self.config.CAMERA_HFLIP = hflip
        self.config.save()
        logging.info(f"Changed camera flip to {vflip} {hflip}")

    def getFrame(self):
        ret, frame = self.camera.read()
        if self.vflip:
            frame = cv2.flip(frame, 0)
        if self.hflip:
            frame = cv2.flip(frame, 1)
        logging.debug(f"Got frame: {ret}")
        return (ret, frame)
    
    def close(self):
        if self.camera is not None:
            self.camera.release()
            logging.info("Camera {self.nowCameraIndex} closed")
    
    def start(self):
        self.camera = cv2.VideoCapture(self.availableCameras[self.nowCameraIndex])
        self.updateCameraSettings()
        logging.info(f"Camera {self.nowCameraIndex} started")

    def __del__(self):
        if self.camera is not None:
            self.camera.release()
            logging.info(f"Camera {self.nowCameraIndex} deleted")
