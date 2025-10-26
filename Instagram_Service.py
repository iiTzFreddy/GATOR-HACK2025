"""
instagram_service.py
- Drop-in Instagram carousel publishing (image + video + caption)
- Can run as a FastAPI microservice OR import and call publish() directly

Requirements:
  pip install fastapi uvicorn requests python-dotenv
Environment:
  IG_ACCESS_TOKEN=...   # long-lived token with instagram_content_publish
  IG_USER_ID=1784...    # your Instagram Business/Creator user id
"""
import os
import time
from typing import List, Tuple, Optional, Dict

import requests
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

#Env
load_dotenv()
GRAPH_BASE = "https://graph.facebook.com/v20.0"
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

#Errors
class IGError(RuntimeError):
    pass
def _require_env() -> None:
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        raise IGError("Missing IG_ACCESS_TOKEN or IG_USER_ID in environment")

#HTTP Helpers
def _post(path: str, data: dict) -> dict:
    resp = requests.post(f"{GRAPH_BASE}/{path}", data = data, timeout = 60)
    if not resp.ok:
        raise IGError(f"POST {path} failed: {resp.status_code} {resp.text}")
    return resp.json()

def _get(path: str, params: dict) -> dict:
    resp = requests.get(f"{GRAPH_BASE}/{path}", params = params, timeout = 60)
    if not resp.ok:
        raise IGError(f"GET {path} failed: {resp.status_code} {resp.text}")
    return resp.json()

#Container creation
def create_image_child(image_url: str) -> str:
    "Create an IMAGE child container for a carousel. image_url MUST be publicly reachable (HTTPS)"
    _require_env()
    data = {"access_token": IG_ACCESS_TOKEN, "image_url": image_url, "is_carousel_item": "true"}
    res = _post(f"{IG_USER_ID}/media", data)
    return res["id"]

def create_video_child(video_url: str) -> str:
    "Create a VIDEO child container for a carousel. video_url MUST be publicly reachable (HTTPS)"
    _require_env()
    data = {"access_token": IG_ACCESS_TOKEN, "video_url": video_url, "media_type": "VIDEO", "is_carousel_item": "true"}
    res = _post(f"{IG_USER_ID}/media", data)
    return res["id"]

def wait_until_finished(container_id: str, poll_every: int = 3, timeout: int = 240) -> None:
    """
    Poll a VIDEO container until status_code == FINISHED.
    """
    _require_env()
    t0 = time.time()
    while True:
        res = _get(container_id, {
            "access_token": IG_ACCESS_TOKEN,
            "fields": "status_code"
        })
        status = res.get("status_code")
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise IGError(f"Container {container_id} status={status}")
        if time.time() - t0 > timeout:
            raise IGError(f"Timeout waiting for container {container_id} to finish.")
        time.sleep(poll_every)

def create_carousel(child_ids: List[str], caption: str) -> str:
    #Create a CAROUSEL container with given child container ids and caption
    _require_env()
    children_str = ",".join(child_ids)
    data = {
        "access_token": IG_ACCESS_TOKEN,
        "media_type": "CAROUSEL",
        "children": children_str,
        "caption": caption
    }
    res = _post(f"{IG_USER_ID}/media", data)
    return res["id"]

def publish_container(creation_id: str) -> str:
    #Publish a previously created container (image/video/carousel)
    _require_env()
    data = {"access_token": IG_ACCESS_TOKEN, "creation_id": creation_id}
    res = _post(f"{IG_USER_ID}/media_publish", data)
    return res["id"]

#Public API
def publish_image_plus_video_carousel(
    image_url: str, video_url: str, caption: str
) -> Dict[str, str]:
    #Create image child, create video child and wait for FINISHED, create carousel container (with caption), publish carousel. Returns dict with child ids and published media id
    img_id = create_image_child(image_url)
    vid_id = create_video_child(video_url)
    wait_until_finished(vid_id) #Only need to wait for video child
    carousel_id = create_carousel([img_id, vid_id], caption)
    media_id = publish_container(carousel_id)
    return {
        "image_child_id": img_id,
        "video_child_id": vid_id,
        "carousel_id": carousel_id,
        "published_media_id": media_id,
    }

#FastAPI app
app = FastAPI(title = "Instagram Publisher")
@app.post("/instagram/publish")
async def instagram_publish(
    image_url: str = Form(..., description="Publicly reachable HTTPS URL of the image"),
    video_url: str = Form(..., description="Publicly reachable HTTPS URL of the video"),
    caption: str = Form("", description="Caption for the carousel post")
):
    """
    Publish an Instagram carousel post with one image and one video.

    Parameters:
    - image_url: Publicly reachable HTTPS URL of the image
    - video_url: Publicly reachable HTTPS URL of the video
    - caption: Caption for the carousel post

    Returns:
    - JSON with IDs of created containers and published media
    """
    try:
        out = publish_image_plus_video_carousel(image_url, video_url, caption)
        return JSONResponse(content=result)
    except IGError as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
