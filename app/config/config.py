import os
import yaml
import logging

class Config:
    def __init__(self, path='config.yaml'):
        newDict = self.loadConfig(path)
        if newDict:
            self.__dict__.update(newDict)

    def loadConfig(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'r') as file:
                    return yaml.safe_load(file)
        except Exception as e:
            logging.error(f'Error loading config: {e}')
            raise e

    def save(self, path='config.yaml'):
        with open(path, 'w') as file:
            yaml.dump(self.__dict__, file)

    CAMERA_RESOLUTION = (640, 480)
    CAMERA_FPS = 30
    CAMERA_SEARCH_LIMIT = 10
    CAMERA_INDEX = 0
    CAMERA_VFLIP = False
    CAMERA_HFLIP = False