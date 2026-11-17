from __future__ import annotations
import asyncio
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .model_client import ModelClient
from .frame_processing import LandmarkProcessor
from . import store

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
load_dotenv(ROOT / ".env")
model_client = ModelClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_db()
    yield

app = FastAPI(
    title="SanketSetu API",
    version="1.0.0",
    description="Accessible Indian Sign Language learning and live recognition platform.",
    lifespan=lifespan,
)
app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")


class HistoryCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str = Field(default="live", max_length=20)

class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    message: str = Field(default="", max_length=2000)


@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(FRONTEND / "manifest.webmanifest", media_type="application/manifest+json")

@app.get("/sw.js")
async def service_worker():
    return FileResponse(FRONTEND / "sw.js", media_type="application/javascript")

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "SanketSetu", "version": app.version}

@app.get("/api/config")
async def config():
    return {
        "app_name": "SanketSetu",
        "model_configured": model_client.configured,
        "model_provider": model_client.provider,
        "model": model_client.health(),
        "recognition_clip_frames": 16,
        "recognition_input_size": "224x224",
        "mode": "experimental" if model_client.provider == "gemini_experimental" else ("live" if model_client.configured else "not_configured"),
        "privacy": "Camera frames are streamed to the configured inference backend and are not stored by this application.",
    }

@app.get("/api/resources")
async def resources():
    return {
        "resources": [
            {"title": "Official ISL Dictionary", "description": "Government of India's Indian Sign Language Dictionary with video demonstrations and English/Hindi equivalents.", "url": "https://divyangjan.depwd.gov.in/islrtc/", "source": "ISLRTC / Department of Empowerment of Persons with Disabilities"},
            {"title": "ISLRTC Learning Resources", "description": "Courses, dictionaries, videos and learning material from the national ISL resource centre.", "url": "https://islrtc.nic.in/", "source": "Government of India"},
            {"title": "DIKSHA", "description": "Educational resources, including Indian Sign Language learning content.", "url": "https://diksha.gov.in/", "source": "Ministry of Education, Government of India"},
            {"title": "ISLRTC YouTube", "description": "Official sign language video resources.", "url": "https://www.youtube.com/@islrtcnewdelhi4069", "source": "ISLRTC"},
        ]
    }

@app.get("/api/history")
async def history(limit: int = 100):
    return {"items": store.get_history(limit)}

@app.post("/api/history", status_code=201)
async def create_history(item: HistoryCreate):
    return store.save_history(item.text.strip(), item.confidence, item.source)

@app.delete("/api/history/{item_id}")
async def remove_history(item_id: int):
    if not store.delete_history(item_id):
        raise HTTPException(status_code=404, detail="History item not found")
    return {"deleted": True}

@app.delete("/api/history")
async def wipe_history():
    return {"deleted": store.clear_history()}

@app.post("/api/feedback", status_code=201)
async def feedback(item: FeedbackCreate):
    if not item.message.strip():
        raise HTTPException(status_code=422, detail="Please add a short feedback message.")
    return store.save_feedback(item.rating, item.message.strip())


@app.websocket("/ws/translate")
async def translate_socket(websocket: WebSocket):
    await websocket.accept()
    processor = LandmarkProcessor()
    frames: deque[bytes] = deque()
    frame_count = 0
    last_notice = 0.0
    try:
        await websocket.send_json({
            "type": "ready",
            "model_configured": model_client.configured,
            "landmarks_enabled": processor.available,
            "landmark_status": processor.reason,
            "clip_frames": 16,
            "message": "Camera connection ready. Start streaming when you are ready.",
        })
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if message.get("bytes") is not None:
                raw = message["bytes"]
                if not raw or len(raw) > 1_000_000 or not raw.startswith(b"\xff\xd8"):
                    await websocket.send_json({"type": "error", "message": "Invalid JPEG frame or frame exceeds 1 MB."})
                    continue
                try:
                    prepared = await asyncio.to_thread(processor.process, raw)
                except Exception as exc:
                    await websocket.send_json({"type": "error", "message": f"Frame processing failed: {exc}"})
                    continue
                frames.append(prepared)
                frame_count += 1
                if len(frames) >= 16:
                    clip = list(frames)[:16]
                    if not model_client.configured:
                        now = time.monotonic()
                        if now - last_notice > 5:
                            await websocket.send_json({
                                "type": "model_unavailable",
                                "message": "AI inference is not connected. Set GEMINI_API_KEY for experimental Gemini vision or MODEL_API_BASE_URL for a compatible ISL model. No prediction has been generated.",
                            })
                            last_notice = now
                    else:
                        try:
                            result = await asyncio.to_thread(model_client.predict, clip)
                            label = result["label"].strip()
                            if label:
                                await websocket.send_json({"type": "prediction", **result, "sequence": frame_count})
                        except Exception as exc:
                            await websocket.send_json({"type": "model_error", "message": str(exc)})
                    # 16-frame window with 6-frame stride.
                    for _ in range(min(6, len(frames))):
                        frames.popleft()
                if frame_count % 20 == 0:
                    await websocket.send_json({"type": "stream_status", "frames_received": frame_count, "buffered_frames": len(frames)})
            elif message.get("text"):
                # Small control protocol: ping, stop, and end-of-stream.
                import json
                try:
                    payload = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue
                if payload.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif payload.get("type") == "stop":
                    frames.clear()
                    frame_count = 0
                    await websocket.send_json({"type": "stopped", "message": "Stream buffer cleared."})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        processor.close()
        try:
            await websocket.close()
        except Exception:
            pass
