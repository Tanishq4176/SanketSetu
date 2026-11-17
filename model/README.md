# Model integration — setup information

SanketSetu supports custom dedicated ISL inference services as well as experimental Gemini vision. Obtain or deploy a compatible inference service before enabling dedicated model recognition.

## Required service contract

Configure `.env`:

```dotenv
MODEL_API_BASE_URL=https://YOUR-MODEL-SERVICE.example
```

The service must implement:

```http
POST /predict_frames_bin?top_k=5
Content-Type: application/octet-stream
```

Request body: ISLF binary frame container containing exactly 16 JPEG frames. See `backend/frame_codec.py`.

Expected JSON response:

```json
{
  "prediction": "hello",
  "confidence": 0.91,
  "inference_time_ms": 230
}
```

`confidence` and latency fields are optional. At minimum, provide `prediction` or `label`.

The base URL may include `/predict_frames_bin`; if omitted, the backend appends it. The status check assumes a `/health` endpoint at the service root. If the model server does not implement `/health`, its health badge may remain unavailable even while its prediction route works; use the actual prediction response and logs as the source of truth.

## Preprocessing requirement

The inference pipeline uses 16 frames, resized to 224×224 and landmark processing with MediaPipe. SanketSetu's optional `LandmarkProcessor` applies pose/hand overlays when the task models are installed. If this is unavailable, the service receives raw 224×224 frames.
