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

resolutionOptions = [(640, 480), (1280, 720), (1920, 1080)]
fpsOptions = [30, 60]
preViewResolutionOptions = [(640, 480), (1280, 720), (1920, 1080)]
modeOptions = ["record", "stream"]
mode = "record"

camera = None


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
        import picamera

        try:
            global camera
            camera = picamera.PiCamera()
            camera.resolution = config.resolution
            camera.framerate = config.fps
            camera.vflip = True
            camera.hflip = True
            camera.start_preview()
            camera.preview.resolution = config.preViewResolution
        except Exception as e:
            print(e)
            raise e
    except ImportError:
        print("picamera not found")
        raise ImportError
    finally:
        pass
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
        "resolution": camera.resolution,
        "fps": config.fps,
        "preViewResolution": config.preViewResolution,
        "hflip": camera.hflip,
        "vflip": camera.vflip,
    }


@app.post("/config")
def setConfig(configRequest: ConfigRequest):
    if configRequest.resolution is not None:
        camera.resolution = configRequest.resolution
        config.resolution = configRequest.resolution
    if configRequest.fps is not None:
        camera.framerate = configRequest.fps
        config.fps = configRequest.fps
    if configRequest.preViewResolution is not None:
        camera.preview.resolution = configRequest.preViewResolution
        config.preViewResolution = configRequest.preViewResolution
    if configRequest.hflip is not None:
        camera.hflip = configRequest.hflip
        config.hflip = configRequest.hflip
    if configRequest.vflip is not None:
        camera.vflip = configRequest.vflip
        config.vflip = configRequest.vflip
    return {
        "resolution": camera.resolution,
        "fps": config.fps,
        "preViewResolution": config.preViewResolution,
        "hflip": camera.hflip,
        "vflip": camera.vflip,
    }


@app.post("/start")
def startCamera():
    camera.start_preview()
    return {"status": "started"}


@app.post("/stop")
def stopCamera():
    camera.stop_preview()
    return {"status": "stopped"}


@app.post("/capture")
def captureImage():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"./image/{timestamp}.jpg"
    camera.capture(filename)

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


class MP4Outputer(object):
    def __init__(self, path: Union[str, Path]):
        print("MP4saverOutput")
        self.converter = Popen(
            [
                "ffmpeg",
                "-f",
                "h264",
                "-i",
                "-",
                "-vcodec",
                "copy",
                "-f",
                "mp4",
                "-y",
                str(path),
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=False,
            close_fds=True,
        )

    def write(self, data: bytes):
        self.converter.stdin.write(data)

    def flush(self):
        self.converter.stdin.close()
        self.converter.wait()


@app.post("/record")
def recordVideo():
    if camera.recording:
        raise Exception("Recording")
    if mode == "stream":
        raise Exception("Streaming")
    global MP4Output
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"./video/{timestamp}.mp4"
    MP4Output = MP4Outputer(filename)
    camera.start_recording(MP4Output, format="h264")
    return {"status": "recording"}


@app.post("/stopRecord")
def stopRecordVideo():
    if not camera.recording:
        raise Exception("Not Recording")
    if mode == "stream":
        raise Exception("Streaming")
    camera.stop_recording()
    return {"status": "stopped"}


@app.get("/record")
def getRecordStatus():
    return {"status": camera.recording, "recordlist": os.listdir("./video")}


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


class BroadcastOutput(object):
    def __init__(self, camera):
        print("Spawning background conversion process")
        self.converter = Popen(
            [
                "ffmpeg",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "yuv420p",
                "-s",
                "%dx%d" % camera.resolution,
                "-r",
                str(float(camera.framerate)),
                "-i",
                "-",
                "-f",
                "mpeg1video",
                "-b",
                "1500k",
                "-r",
                str(float(camera.framerate)),
                "-",
            ],
            stdin=PIPE,
            stdout=PIPE,
            shell=False,
            close_fds=True,
        )

    def write(self, b):
        self.converter.stdin.write(b)

    def flush(self):
        print("Waiting for background conversion process to exit")
        self.converter.stdin.close()
        self.converter.wait()


class BroadcastThread(Thread):
    def __init__(self, converter, manager):
        super(BroadcastThread, self).__init__()
        self.converter = converter
        self.manager = manager

    def run(self):
        async def broadcast_loop():
            try:
                while True:
                    buf = self.converter.stdout.read1(32768)
                    if buf:
                        try:
                            mutex.acquire()
                            await self.manager.broadcast(buf)
                        finally:
                            mutex.release()
                    elif self.converter.poll() is not None:
                        break
            finally:
                self.converter.stdout.close()

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
    if camera.recording and mode == "record" and req.mode == "stream":
        raise Exception("Recording")

    if req.mode == "stream" and mode == "record":
        mode = req.mode
        global broadcastOutput
        broadcastOutput = BroadcastOutput(camera)
        global broadcastThread
        broadcastThread = BroadcastThread(broadcastOutput.converter, manager)
        camera.start_recording(broadcastOutput, format="yuv")
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

    uvicorn.run(app, host="0.0.0.0", port=80)
