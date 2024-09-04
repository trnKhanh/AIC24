import os
import sys
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException

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

@app.get("/api/search")
async def search(
    model: str = MODEL_DEFAULT,
    q: str = "",
    offset: int = 0,
    limit: int = 50,
    nprob: int = 8,
):
    text_features = clip_models[model].get_text_features([q])[0].tolist()
    res = database.search(text_features, "", offset, limit, nprob, model)
    videos = []
    for record in res[0]:
        data = record["entity"]
        video_frame_str = data["frame_id"]
        video_id, frame_id = video_frame_str.split("#")
        video_uri = WORK_DIR / "videos" / f"{video_id}.mp4"
        videos.append(
            dict(video_id=video_id, frame_id=frame_id, video_uri=video_uri)
        )

    return {"videos": videos}

@app.get("/api/similar")
async def similar(
    video_id: str,
    frame_id: int,
    model: str = MODEL_DEFAULT,
    offset: int = 0,
    limit: int = 50,
    nprob: int = 8,
):
    record = database.get(f"{video_id}#{frame_id}")
    if len(record) == 0:
        raise HTTPException(status_code=404, detail="Frame not found")

    image_features = record[0][f"feature_{model}"]

    res = database.search(image_features, "", offset, limit, nprob, model)
    videos = []
    for record in res[0]:
        data = record["entity"]
        video_frame_str = data["frame_id"]
        video_id, frame_id = video_frame_str.split("#")
        video_uri = WORK_DIR / "videos" / f"{video_id}.mp4"
        videos.append(
            dict(video_id=video_id, frame_id=frame_id, video_uri=video_uri)
        )

    return {"videos": videos}
