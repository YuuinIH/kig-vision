import os
import yaml

class Config:
    def __init__(self, path='config.yaml'):
        self.__dict__ = self.loadConfig(path)

    def loadConfig(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'r') as file:
                    return yaml.safe_load(file)
        except Exception as e:
            print(e)
            return self.__dict__

    def save(self, path='config.yaml'):
        with open(path, 'w') as file:
            yaml.dump(self.__dict__, file)

    CAMERA_RESOLUTION = (640, 480)
    CAMERA_FPS = 30
    CAMERA_SEARCH_LIMIT = 10
    CAMERA_INDEX = 0
    CAMERA_VFLIP = False
    CAMERA_HFLIP = False