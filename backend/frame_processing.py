"""Video-frame preparation with optional MediaPipe landmark overlays.

When the .task models are unavailable, the frame is still normalized and sent
without overlays; the UI/health endpoint reports this limitation explicitly.
"""
from __future__ import annotations
import io
from pathlib import Path
from PIL import Image, ImageOps

FRAME_SIZE = (224, 224)


class LandmarkProcessor:
    def __init__(self, model_dir: str | Path | None = None):
        self.pose = None
        self.hands = None
        self.available = False
        self.reason = "MediaPipe task models are not installed. Raw frames will be used."
        self._mp = None
        model_dir = Path(model_dir or Path(__file__).parent / "models")
        pose_path = model_dir / "pose_landmarker_full.task"
        hand_path = model_dir / "hand_landmarker.task"
        if not pose_path.exists() or not hand_path.exists():
            self.reason = f"Missing MediaPipe assets in {model_dir}. Raw frames will be used."
            return
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            self._mp = mp
            base = python.BaseOptions
            self.pose = vision.PoseLandmarker.create_from_options(
                vision.PoseLandmarkerOptions(base_options=base(model_asset_path=str(pose_path)))
            )
            self.hands = vision.HandLandmarker.create_from_options(
                vision.HandLandmarkerOptions(base_options=base(model_asset_path=str(hand_path)), num_hands=2)
            )
            self.vision = vision
            self.drawing = vision.drawing_utils
            self.styles = vision.drawing_styles
            self.available = True
            self.reason = "MediaPipe pose and hand landmarkers are active."
        except Exception as exc:
            self.reason = f"MediaPipe initialization failed: {exc}. Raw frames will be used."
            self.close()

    def process(self, jpeg: bytes) -> bytes:
        with Image.open(io.BytesIO(jpeg)) as original:
            image = original.convert("RGB")
        if self.available:
            try:
                import numpy as np
                import cv2
                mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=np.asarray(image))
                pose_result = self.pose.detect(mp_image) if self.pose else None
                hand_result = self.hands.detect(mp_image) if self.hands else None
                frame = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
                if pose_result and pose_result.pose_landmarks:
                    for landmarks in pose_result.pose_landmarks:
                        self.drawing.draw_landmarks(
                            frame, landmarks,
                            self.vision.PoseLandmarksConnections.POSE_LANDMARKS,
                            self.styles.get_default_pose_landmarks_style(),
                        )
                if hand_result and hand_result.hand_landmarks:
                    for landmarks in hand_result.hand_landmarks:
                        self.drawing.draw_landmarks(
                            frame, landmarks,
                            self.vision.HandLandmarksConnections.HAND_CONNECTIONS,
                            self.styles.get_default_hand_landmarks_style(),
                            self.styles.get_default_hand_connections_style(),
                        )
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            except Exception:
                # Do not crash the stream because landmark visualization failed.
                pass
        image = ImageOps.fit(image, FRAME_SIZE, method=Image.Resampling.BILINEAR, centering=(0.5, 0.5))
        out = io.BytesIO()
        image.save(out, format="JPEG", quality=80, optimize=True)
        return out.getvalue()

    def close(self):
        for detector in (self.pose, self.hands):
            if detector is not None:
                try:
                    detector.close()
                except Exception:
                    pass
        self.pose = None
        self.hands = None
        self.available = False
