import os
import sys
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Header, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from ...index import MilvusDatabase
from ...analyse.features import CLIP
from ....config import GlobalConfig

WORK_DIR = Path(os.getenv("AIC51_WORK_DIR") or ".")
logger = logging.getLogger(__name__)

clip_models = {}
for model in GlobalConfig.get("webui", "features") or []:
    model_name = model["name"]
    pretrained_model = model["pretrained_model"]
    clip_models[model_name] = CLIP(pretrained_model)
if len(clip_models) == 0:
    logger.error(
        f'No models found in "{GlobalConfig.CONFIG_FILE}". Check your "{GlobalConfig.CONFIG_FILE}"'
    )
MODEL_DEFAULT = list(clip_models.keys())[0]

database = MilvusDatabase(GlobalConfig.get("webui", "databse") or "milvus")

app = FastAPI()
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/search")
async def search(
    request: Request,
    model: str = MODEL_DEFAULT,
    q: str = "",
    offset: int = 0,
    limit: int = 50,
    nprobe: int = 8,
):
    text_features = clip_models[model].get_text_features([q])[0].tolist()
    res = database.search(text_features, "", offset, limit, nprobe, model)
    frames = []
    for record in res[0]:
        data = record["entity"]
        video_frame_str = data["frame_id"]
        video_id, frame_id = video_frame_str.split("#")
        frame_uri = (
            f"{request.base_url}api/files/keyframes/{video_id}/{frame_id}.png"
        )
        video_uri = f"{request.base_url}api/stream/videos/{video_id}.mp4"
        frames.append(
            dict(
                id=video_frame_str,
                video_id=video_id,
                frame_id=frame_id,
                frame_uri=frame_uri,
                video_uri=video_uri,
            )
        )

    return {"total": database.get_total(), "frames": frames}


@app.get("/api/similar")
async def similar(
    request: Request,
    id: str,
    model: str = MODEL_DEFAULT,
    offset: int = 0,
    limit: int = 50,
    nprobe: int = 8,
):
    record = database.get(id)
    if len(record) == 0:
        raise HTTPException(status_code=404, detail="Frame not found")

    image_features = record[0][f"feature_{model}"]

    res = database.search(image_features, "", offset, limit, nprobe, model)
    frames = []
    for record in res[0]:
        data = record["entity"]
        video_frame_str = data["frame_id"]
        video_id, frame_id = video_frame_str.split("#")
        frame_uri = (
            f"{request.base_url}api/files/keyframes/{video_id}/{frame_id}.png"
        )
        video_uri = f"{request.base_url}api/stream/videos/{video_id}.mp4"
        frames.append(
            dict(
                id=video_frame_str,
                video_id=video_id,
                frame_id=frame_id,
                frame_uri=frame_uri,
                video_uri=video_uri,
            )
        )

    return {"total": database.get_total(), "frames": frames}


@app.get("/api/frame_info")
async def frame_info(request: Request, video_id: str, frame_id: str):
    id = f"{video_id}#{frame_id}"
    record = database.get(id)
    frame_uri = (
        f"{request.base_url}api/files/keyframes/{video_id}/{frame_id}.png"
    )
    video_uri = f"{request.base_url}api/stream/videos/{video_id}.mp4"
    return dict(
        id=id if len(record) > 0 else None,
        video_id=video_id,
        frame_id=frame_id,
        frame_uri=frame_uri if len(record) > 0 else None,
        video_uri=video_uri,
    )


@app.get("/api/files/{file_path:path}")
async def get_file(file_path):
    return FileResponse(str(WORK_DIR / file_path))


CHUNK_SIZE = 1024 * 1024


@app.get("/api/stream/{file_path:path}")
async def video_endpoint(file_path: str, range: str = Header(None)):
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    video_path = Path(file_path)
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = video_path.stat().st_size
        headers = {
            "Content-Range": f"bytes {str(start)}-{str(min(end, filesize-1))}/{str(filesize)}",
            "Accept-Ranges": "bytes",
        }
    return Response(
        data, status_code=206, headers=headers, media_type="video/mp4"
    )

@app.get("/api/models")
async def models():
    return {"models": list(clip_models.keys())}


app.mount(
    "/assets",
    StaticFiles(directory=WORK_DIR / ".dist/assets"),
    "assets",
)


@app.get("/{rest_of_path:path}")
async def client_app():
    return FileResponse(WORK_DIR / ".dist/index.html")
