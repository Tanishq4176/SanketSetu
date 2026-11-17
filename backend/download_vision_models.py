"""Download official MediaPipe Tasks model assets required for landmark overlays."""
from pathlib import Path
import requests

MODELS = {
    "pose_landmarker_full.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
}


def main():
    destination = Path(__file__).parent / "models"
    destination.mkdir(parents=True, exist_ok=True)
    for filename, url in MODELS.items():
        path = destination / filename
        if path.exists() and path.stat().st_size > 100_000:
            print(f"Already present: {path}")
            continue
        print(f"Downloading {filename} …")
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        if len(response.content) < 100_000:
            raise RuntimeError(f"Download for {filename} looks incomplete ({len(response.content)} bytes).")
        path.write_bytes(response.content)
        print(f"Saved {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
