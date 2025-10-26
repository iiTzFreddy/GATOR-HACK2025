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
IG_ACCESS_TOKEN = os.getenv("IG ACCESS TOKEN")
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
        raise IGError(f"GET {path} failed: {resp.status_code} {resp.text}")
    return resp.json()

#Container creation
def create_image_child(image_url: str) -> str:
    "Create an IMAGE child container for a carousel. image_url MUST be publicly reachable (HTTPS)"
    _require_env()
    data = {"access_token": IG_ACCESS_TOKEN, "image_url": image_url, "is_carousel_item": "true"}
    res = _post(f"{IG_USER_ID}/media", data)
    return res["id"]

def publish_container(creation_id: str) -> str:
    #Publish a previously created container (image/video/carousel)
    _require_env()
    data = {"access token": IG_ACCESS_TOKEN, "creation_id": creation_id}
    res = _post(f"{IG_USER_ID}/media_publish", data)
    return res["id"]

#Public API
def publish_image_plus_video_carousel(
    image_url: str, video_url: str, caption: str
) -> Dict[str, str]:
    #Create image child, create video child and wait for FINISHED, create carousel container (with caption), publish carousel. Returns dict with child ids and published media id
    img_id = create_image_child(image_url)
    vid_id = create_video_child(video_url)
    wait_until_finished(vid_id)
    carousel_id = create_carousel([img_id, vid_id], caption)
    media_id = publish_container(carousel_id)
    return {
        "image_child_id": img_id,
        "video_child_id": vid_id,
        "carousel_id": carousel_id,
        "published_media_id": media_id,
    }
    
