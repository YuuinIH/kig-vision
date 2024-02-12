import asyncio
from contextlib import asynccontextmanager
import datetime
import io
import json
import os
from struct import Struct
from threading import Thread
import threading
from typing import Any, Union
from anyio import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from subprocess import PIPE, Popen
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from subprocess import PIPE, Popen
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
from picamera2 import Picamera2,Preview
from picamera2.previews.qt import QPicamera2
from picamera2.encoders import H264Encoder,MJPEGEncoder
from picamera2.outputs import FfmpegOutput,FileOutput
from libcamera import Transform
from PyQt5.QtWidgets import QApplication,QWidget

os.putenv('DISPLAY',":0")

resolutionOptions = [(640, 480), (1280, 720), (1920, 1080)]
fpsOptions = [30, 60]
preViewResolutionOptions = [(640, 480), (1280, 720), (1920, 1080)]
modeOptions = ["record", "stream"]
mode = "record"
recording=False

camera = None
qtapp = None

class FullScreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('全屏窗口')
        self.setGeometry(100, 100, 500, 500)


class Config(object):
    def __init__(self) -> None:
        self.__dict__["resolution"] = (640, 480)
        self.__dict__["fps"] = 30
        self.__dict__["preViewResolution"] = (640, 480)
        self.__dict__["hflip"] = False
        self.__dict__["vflip"] = False
        print("init config")
        if os.path.exists("config.json"):
            self.load()

    def __setattr__(self, __name: str, __value: Any) -> None:
        self.__dict__[__name] = __value
        self.save()

    def save(self):
        print("save config")
        io.open("config.json", "w").write(json.dumps(self.__dict__))

    def load(self):
        if os.path.exists("config.json"):
            print("load config")
            oldconfig = json.loads(io.open("config.json", "r").read())
            for key in oldconfig:
                self.__dict__[key] = oldconfig[key]
        else:
            print("config not found")
            self.save()


config = Config()

if os.path.exists("./image") == False:
    os.mkdir("./image")
if os.path.exists("./video") == False:
    os.mkdir("./video")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        global camera,qtapp
        qtapp = QApplication([])
        camera=Picamera2()
        camera_config= camera.create_preview_configuration(main=
            {
                "size": config.resolution,
            }
        )
        camera.configure(camera_config)
        qpicamera2 = QPicamera2(camera, keep_ar=False)
        qpicamera2.showFullScreen()
        camera.start()
        qpicamera2.show()
    except Exception as e:
        print(e)
        raise e
    yield
    if camera != None:
        camera.close()
        camera = None


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfigRequest(BaseModel):
    resolution: Optional[tuple]
    fps: Optional[int]
    preViewResolution: Optional[tuple]
    hflip: Optional[bool]
    vflip: Optional[bool]


@app.options("/config")
def getOptions():
    return {
        "resolution": resolutionOptions,
        "fps": fpsOptions,
        "preViewResolution": preViewResolutionOptions,
    }


@app.get("/config")
def getConfig():
    return {
        "resolution": config.resolution,
        "fps": config.fps,
        "preViewResolution": config.preViewResolution,
        "hflip": config.hflip,
        "vflip": config.vflip,
    }


@app.post("/config")
def setConfig(configRequest: ConfigRequest):
    newconfig=camera.create_preview_configuration(main=
                {
                    "size": configRequest.resolution,
                }
            )
    camera.configure(newconfig)
    config.resolution = configRequest.resolution
    config.fps = configRequest.fps
    config.preViewResolution = configRequest.preViewResolution
    config.hflip = configRequest.hflip
    config.vflip = configRequest.vflip
    return {
        "resolution": config.resolution,
        "fps": config.fps,
        "preViewResolution": config.preViewResolution,
        "hflip": config.hflip,
        "vflip": config.vflip,
    }


@app.post("/start")
def startCamera():
    camera.start_preview(Preview.QT)
    return {"status": "started"}


@app.post("/stop")
def stopCamera():
    camera.stop_preview()
    return {"status": "stopped"}


@app.post("/capture")
def captureImage():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"./image/{timestamp}.jpg"
    camera.capture_file(filename)

    return {"status": "captured"}


@app.get("/capture")
def getCaptureList():
    return {"capturelist": os.listdir("./image")}


@app.get("/capture/{filename}")
def getCapture(filename: str):
    return FileResponse(f"./image/{filename}")


@app.delete("/capture/{filename}")
def deleteCapture(filename: str):
    os.remove(f"./image/{filename}")
    return {"status": "deleted"}


class deleteCaptures(BaseModel):
    filename: list


@app.post("/deleteCaptures")
def deleteCaptures(req: deleteCaptures):
    for filename in req.filename:
        os.remove(f"./image/{filename}")
    return {"status": "deleted"}


@app.post("/record")
def recordVideo():
    if recording:
        raise Exception("Recording")
    if mode == "stream":
        raise Exception("Streaming")
    global MP4Output
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"./video/{timestamp}.mp4"
    encoder = H264Encoder(10000000)
    output = FfmpegOutput(filename)
    camera.start_recording(encoder,output)
    recording=True
    return {"status": "recording"}


@app.post("/stopRecord")
def stopRecordVideo():
    if not recording:
        raise Exception("Not Recording")
    if mode == "stream":
        raise Exception("Streaming")
    camera.stop_recording()
    recording=False
    return {"status": "stopped"}


@app.get("/record")
def getRecordStatus():
    return {"status": recording, "recordlist": os.listdir("./video")}


@app.get("/record/{filename}")
def getRecord(filename: str):
    return FileResponse(f"./video/{filename}")


@app.delete("/record/{filename}")
def deleteRecord(filename: str):
    os.remove(f"./video/{filename}")
    return {"status": "deleted"}


class deleteRecords(BaseModel):
    filename: list


@app.post("/deleteRecords")
def deleteRecords(req: deleteRecords):
    for filename in req.filename:
        os.remove(f"./video/{filename}")
    return {"status": "deleted"}


mutex = threading.Lock()
JSMPEG_MAGIC = b"jsmp"
JSMPEG_HEADER = Struct(">4sHH")

class BroadcastThread(Thread):
    def __init__(self, file:io.BufferedIOBase, manager):
        super(BroadcastThread, self).__init__()
        self.file = file
        self.manager = manager

    def run(self):
        async def broadcast_loop():
            try:
                while True:
                    buf = self.file.read1(32768)
                    if buf:
                        try:
                            mutex.acquire()
                            await self.manager.broadcast(buf)
                        finally:
                            mutex.release()
                    elif self.converter.poll() is not None:
                        break
            finally:
                self.file.close()

        asyncio.run(broadcast_loop())


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        try:
            mutex.acquire()
            self.active_connections.append(websocket)
        finally:
            mutex.release()
        await websocket.send_bytes(
            JSMPEG_HEADER.pack(JSMPEG_MAGIC, camera.resolution[0], camera.resolution[1])
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: bytes):
        for connection in self.active_connections:
            try:
                await connection.send_bytes(message)
            except WebSocketDisconnect as e:
                self.disconnect(connection)
            # TODO: Unexpected ASGI message 'websocket.send', after sending 'websocket.close' or response already completed.
            except Exception as e:
                self.disconnect(connection)

    def disconnectAll(self):
        for connection in self.active_connections:
            self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws")
async def stream_ws(websocket: WebSocket):
    await manager.connect(websocket)
    if mode != "stream":
        raise Exception("Not Streaming")

    try:
        while True:
            data = await websocket.receive_bytes()
    except WebSocketDisconnect:
        try:
            mutex.acquire()
            manager.disconnect(websocket)
        finally:
            mutex.release()


class modeRequest(BaseModel):
    mode: str


@app.post("/mode")
def setMode(req: modeRequest):
    global mode
    if not req.mode in modeOptions:
        raise Exception("Invalid mode")
    if recording and mode == "record" and req.mode == "stream":
        raise Exception("Recording")

    if req.mode == "stream" and mode == "record":
        mode = req.mode
        global broadcastThread
        buf = io.BufferedIOBase()
        broadcastThread = BroadcastThread(buf , manager)
        encoder = MJPEGEncoder(1000000)
        camera.start_recording(encoder,FileOutput(buf))
        broadcastThread.start()
    elif req.mode == "record" and mode == "stream":
        mode = req.mode
        camera.stop_recording()
        broadcastThread.join()
        manager.disconnectAll()

    return {"status": mode}


@app.get("/mode")
def getMode():
    return {"mode": mode}


@app.get("/stream")
def getStream():
    return FileResponse("web/dist/index.html", media_type="text/html")

app.mount("/", StaticFiles(directory="web/dist", html=True), name="web")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
