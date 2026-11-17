# Architecture

## High-level system

```text
┌───────────────────────────────────────────┐
│ Browser / installable PWA                 │
│                                           │
│ Dashboard · Learn · Practice · History    │
│ Camera preview · Sentence builder · TTS   │
└──────────────────────┬────────────────────┘
                       │ same-origin HTTP
                       ▼
┌───────────────────────────────────────────┐
│ FastAPI application                       │
│                                           │
│ /api/health  /api/config  /api/resources  │
│ /api/history  /api/feedback                │
│ /ws/translate                              │
└──────┬────────────────┬───────────────────┘
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────────────────┐
│ SQLite       │  │ Frame-processing path    │
│ history      │  │ JPEG → optional MediaPipe│
│ feedback     │  │ → 224×224 JPEG            │
└──────────────┘  └─────────────┬────────────┘
                                │ 16-frame window
                                ▼
                   ┌──────────────────────────┐
                   │ ModelClient              │
                   │ ISLF binary packer       │
                   └─────────────┬────────────┘
                                 │ HTTP POST
                                 ▼
                   ┌──────────────────────────┐
                   │ External ISL model API   │
                   │ /predict_frames_bin      │
                   │ Swin3D-S model expected  │
                   └─────────────┬────────────┘
                                 │ JSON prediction
                                 ▼
                   Browser prediction + sentence
```

## Frontend

The frontend is a small dependency-free PWA. `index.html` provides semantic screen structure, `assets/styles.css` defines the visual system and responsive layouts, and `assets/app.js` manages page navigation, camera access, WebSocket messages, sentence composition, speech, history and practice interactions. The service worker caches shell assets only; API calls and WebSocket traffic are never cached.

### Live camera sequence

1. The user explicitly enables the webcam.
2. The browser shows a local preview.
3. The user explicitly starts recognition.
4. JavaScript samples the preview and converts frames to JPEG binary blobs.
5. Binary JPEG frames are sent to `/ws/translate`.
6. The backend validates each frame, optionally overlays MediaPipe landmarks and resizes to 224×224.
7. The backend retains a 16-frame rolling window. Once full, it submits the window and advances by 6 frames, preserving overlap.
8. `ModelClient` packages the frames in the ISLF format and calls the separately configured inference API.
9. Only a response returned by that service is emitted as a `prediction` WebSocket event.
10. The browser updates the prediction and sentence builder. The user chooses whether to speak or save the sentence.

## ISLF binary payload

The transport follows the documented format used by the reference project:

| Field | Size | Meaning |
|---|---:|---|
| Magic | 4 bytes | ASCII `ISLF` |
| Frame count | 2 bytes | Unsigned little-endian count (16 for inference) |
| Length table | 4 × N bytes | Unsigned little-endian JPEG length for each frame |
| Frame data | Variable | JPEG data concatenated in the same order |

`backend/frame_codec.py` provides pack and unpack functions and tests for malformed payloads.

## Model API contract

`MODEL_API_BASE_URL` identifies a compatible model-service base URL. The client appends `/predict_frames_bin` unless the setting already ends in that route. It posts the binary container with `top_k=5` and `application/octet-stream`.

The expected success response includes `prediction` (or `label`) and may include `confidence` and latency metadata. Errors, unavailable services and missing configuration are surfaced as errors/status messages; the project deliberately does not generate guessed labels.

## Persistence

SQLite stores only user-saved text, optional confidence, creation timestamp and source. It does not store webcam frames. Community feedback is stored in a separate table. The default database path is `backend/data/sanketsetu.sqlite3`; set `SANKETSETU_DB` to override it.

The delivered local prototype is single-machine / local-demo oriented. It does not yet include account authentication, per-user tenancy, encryption-at-rest policy or multi-user production deployment controls.

## Preprocessing compatibility warning

The reference repository describes MediaPipe Pose and Hand Landmarkers and a particular video input path for its recognition model. SanketSetu can optionally apply those landmark overlays when the Python dependency and both `.task` files are available. If unavailable, it sends raw frames after resizing. That fallback is explicitly reported and must not be assumed to reproduce the training preprocessing. Model performance must be evaluated against the exact preprocessing used during training.
