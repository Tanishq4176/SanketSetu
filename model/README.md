# Model integration — important setup information

SanketSetu does not include the original Swin3D model weights or a running model server. The upstream README identifies a Hugging Face model repository:

- https://huggingface.co/Creator-090/isl-swin3d-model

A model repository/weight card is not the same thing as a hosted HTTP inference endpoint. Obtain or deploy a compatible inference service before enabling real recognition.

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

## What is not included

- The upstream model weight file.
- A deployable Hugging Face Space/server URL.
- A validated model runtime environment.
- A verified accuracy report for this SanketSetu build.

Do not paste the Hugging Face model-card URL into `MODEL_API_BASE_URL` and expect an inference endpoint. Do not report the original repository's benchmark as a SanketSetu result.

## Preprocessing requirement

The reference pipeline uses 16 frames, resized to 224×224 and landmark processing with MediaPipe. SanketSetu's optional `LandmarkProcessor` attempts to reproduce a pose/hand overlay step when the task models are installed. If this is unavailable, the service receives raw 224×224 frames. This can reduce compatibility with model training data.

For a proper evaluation, verify the model service's preprocessing code and align frame orientation, crop, frame sampling, colour conversion and landmark drawing with the training pipeline. Do not enable a preprocessing variation without testing it.
