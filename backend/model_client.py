"""ISL inference adapter supporting either a compatible hosted ISL service or Gemini vision.

Gemini mode is an EXPERIMENTAL visual-gesture demo, not a validated ISL translation model.
"""
from __future__ import annotations
import base64
import os
import time
from typing import Any
import requests
from .frame_codec import pack_frames


class ModelClient:
    def __init__(self, base_url: str | None = None, timeout: float = 35.0):
        self.base_url = (base_url if base_url is not None else os.getenv("MODEL_API_BASE_URL", "")).strip().rstrip("/")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
        self.timeout = timeout
        self.session = requests.Session()

    @property
    def provider(self) -> str:
        if self.base_url:
            return "custom_isl"
        if self.gemini_api_key:
            return "gemini_experimental"
        return "none"

    @property
    def configured(self) -> bool:
        return self.provider != "none"

    @property
    def predict_url(self) -> str:
        if not self.base_url:
            return ""
        if self.base_url.endswith("/predict_frames_bin"):
            return self.base_url
        return self.base_url + "/predict_frames_bin"

    def health(self) -> dict[str, Any]:
        if self.base_url:
            health_url = self.base_url
            for suffix in ("/predict_frames_bin", "/predict"):
                if health_url.endswith(suffix):
                    health_url = health_url[:-len(suffix)]
            try:
                response = self.session.get(health_url.rstrip("/") + "/health", timeout=4)
                if response.ok:
                    return {"status": "online", "provider": "custom_isl", "detail": response.json() if response.headers.get("content-type", "").startswith("application/json") else {}}
                return {"status": "unavailable", "provider": "custom_isl", "message": f"Model service returned HTTP {response.status_code}."}
            except requests.RequestException as exc:
                return {"status": "unavailable", "provider": "custom_isl", "message": str(exc)}
        if self.gemini_api_key:
            return {"status": "configured", "provider": "gemini_experimental", "model": self.gemini_model,
                    "message": "Gemini is configured. Predictions are experimental visual guesses, not validated ISL translation."}
        return {"status": "not_configured", "message": "Set MODEL_API_BASE_URL for a compatible ISL service or GEMINI_API_KEY for experimental Gemini vision."}

    def _predict_gemini(self, frames: list[bytes]) -> dict[str, Any]:
        parts: list[dict[str, Any]] = [{"text": (
            "You are assisting an EXPERIMENTAL Indian Sign Language gesture demo. "
            "Inspect these 16 ordered video frames as one short sequence. If a clear, "
            "recognisable single sign is visible, return its most likely short English gloss. "
            "Do not invent a sentence or claim certainty. If the sequence is unclear, return UNKNOWN. "
            "Respond only as JSON: {\\\"label\\\":\\\"short gloss or UNKNOWN\\\",\\\"reason\\\":\\\"brief visual reason\\\"}. "
            "This is not a certified ISL translator; fingerspelling, grammar, motion and context may be missed."
        )}]
        for frame in frames:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(frame).decode("ascii")}})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"
        started = time.perf_counter()
        response = self.session.post(url, headers={"x-goog-api-key": self.gemini_api_key}, json={
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json", "maxOutputTokens": 120}
        }, timeout=self.timeout)
        if response.status_code == 429:
            raise RuntimeError("Gemini free-tier rate limit reached. Wait and try again.")
        if response.status_code in (401, 403):
            raise RuntimeError("Gemini rejected the API key or project permissions. Check GEMINI_API_KEY.")
        response.raise_for_status()
        payload = response.json()
        try:
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            import json
            parsed = json.loads(text)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("Gemini returned an unexpected response. Try again with a clearer gesture.") from exc
        label = str(parsed.get("label", "UNKNOWN")).strip()
        if not label:
            label = "UNKNOWN"
        return {
            "label": label,
            "confidence": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "model": f"Gemini {self.gemini_model} · experimental visual estimate",
            "simulated": False,
            "experimental": True,
            "raw": {"reason": str(parsed.get("reason", ""))[:240]},
        }

    def predict(self, frames: list[bytes]) -> dict[str, Any]:
        if len(frames) != 16:
            raise ValueError("Recognition requires exactly 16 frames per clip.")
        if self.base_url:
            body = pack_frames(frames)
            started = time.perf_counter()
            response = self.session.post(self.predict_url, params={"top_k": 5}, data=body,
                headers={"Content-Type": "application/octet-stream"}, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            label = data.get("prediction") or data.get("label")
            if not label:
                raise RuntimeError("Model service response did not contain a prediction label.")
            try:
                confidence = float(data.get("confidence"))
            except (TypeError, ValueError):
                confidence = None
            return {"label": str(label), "confidence": confidence,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "model": "Configured ISL inference service", "simulated": False,
                    "raw": {k: v for k, v in data.items() if k in {"prediction", "confidence", "top_k", "inference_time_ms", "total_latency_ms"}}}
        if self.gemini_api_key:
            return self._predict_gemini(frames)
        raise RuntimeError("AI model is not configured. Set GEMINI_API_KEY or MODEL_API_BASE_URL in .env.")
