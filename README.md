# SanketSetu

**An accessible Indian Sign Language learning and communication prototype.**

SanketSetu is a student community-service project with three practical goals: make trusted ISL learning material easier to reach, provide a clean camera-based recognition interface that can connect to an ISL model service, and encourage informed communication between Deaf and hearing communities.

> **Important status note:** the PWA, API, local history, practice quiz, official-resource directory, camera capture and WebSocket frame transport are implemented in this project. Real AI sign recognition is **not yet operational out of the box** because the reference repository does not include a deployable inference endpoint or model weights inside this project. Configure a compatible service in `.env` before describing live predictions as working. The UI's optional sample preview is clearly marked as simulated and is not AI output.

## Why this is a new project

The public [Uni-Creator/signBridge](https://github.com/Uni-Creator/signBridge) repository was inspected as a technical reference. SanketSetu has a distinct project identity, new responsive PWA interface, local persistence and history management, vocabulary learning and practice areas, community feedback collection, an explicit model-service adapter, Windows-first setup and new documentation. This project retains compatibility with the reference system's 16-frame ISLF model request format. It is not a claim of original authorship over the upstream model, dataset, benchmark, or repository.

The delivery uses a Progressive Web App rather than the upstream Flutter client so that a student can run the prototype locally in a browser with a smaller setup burden. The backend is FastAPI/Python.

## Features implemented

- Responsive dashboard and application navigation.
- Browser camera permission, live preview, explicit start/stop recognition and JPEG frame streaming.
- Authenticated-free local prototype API; no user account is required for the local demonstration.
- WebSocket protocol with a 16-frame sliding inference window and 6-frame stride.
- Model service adapter for the reference-compatible `/predict_frames_bin` endpoint and ISLF binary container.
- Optional MediaPipe pose and hand landmark overlay processing when the optional dependency and task files are installed.
- Sentence builder, copy, browser text-to-speech and save actions.
- Local SQLite translation history with delete and clear operations.
- Beginner vocabulary directory, phrase-to-dictionary lookup shortcut and practice quiz (vocabulary recall, not sign production assessment).
- Links to official Government of India ISL learning resources.
- Local feedback capture.
- Accessibility preferences for larger text and high contrast.
- PWA manifest and service worker for installation and cached interface assets.
- Backend health endpoint and automatically generated API docs.

## Screens

1. **Overview** — product purpose and entry points.
2. **Live translation** — camera, prediction, confidence display, status, sentence builder and speech.
3. **Learn ISL** — basic vocabulary and official dictionary links.
4. **Practice** — five-question Hindi/English vocabulary recall round.
5. **History** — user-saved local messages.
6. **About & feedback** — project purpose, limitations and feedback form.

## Technology

| Layer | Implementation |
|---|---|
| Frontend | HTML, CSS and JavaScript PWA |
| Backend | FastAPI + Uvicorn |
| Live camera transport | Browser `getUserMedia` + WebSocket binary JPEG frames |
| Frame protocol | ISLF: magic header, frame count, lengths and JPEG payloads |
| Model adapter | Python `requests` client to external inference service |
| Frame preprocessing | Pillow; optional MediaPipe Tasks + OpenCV |
| Persistence | SQLite |
| Speech | Browser Speech Synthesis API |
| Tests | pytest + FastAPI TestClient |

## Run on Windows

The quickest route is to double-click `start_windows.bat`. Follow [SETUP.md](SETUP.md) for details.

Manual commands from the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

- Health: `http://127.0.0.1:8000/api/health`
- Configuration/model status: `http://127.0.0.1:8000/api/config`
- Interactive API docs: `http://127.0.0.1:8000/docs`

## AI inference modes

For a quick experimental prototype, add `GEMINI_API_KEY` to `.env` and optionally set `GEMINI_MODEL=gemini-2.5-flash-lite`. Gemini reviews 16 selected frames and returns a best-effort visual gesture guess. This is **not a validated ISL translation model** and should not be presented as reliable translation or used for accessibility-critical communication. Free-tier limits and data-use terms apply.

For a dedicated trained ISL model, see [model/README.md](model/README.md). The model adapter also supports an inference service that accepts:

```http
POST /predict_frames_bin?top_k=5
Content-Type: application/octet-stream
```

The body is an ISLF container with 16 JPEG frames. The service must return JSON containing `prediction` or `label`, and optionally `confidence`.

Set `MODEL_API_BASE_URL` in `.env` to the service base URL. This dedicated service takes precedence over Gemini when both are configured. The actual weights page mentioned in the upstream README is [Creator-090/isl-swin3d-model on Hugging Face](https://huggingface.co/Creator-090/isl-swin3d-model); a model card or weights repository is not itself proof of a running inference API.

Without either a Gemini key or a dedicated model endpoint, camera streaming and the rest of the app still work, but the app reports that AI inference is unavailable. The one-click sample preview is deliberately marked simulated and must not be included as a recognition result in evaluation metrics.

## Optional MediaPipe assets

See [SETUP.md](SETUP.md#6-optional-mediapipe-landmark-preprocessing). The optional installer downloads pose and hand `.task` assets from Google's MediaPipe model storage. If MediaPipe cannot be initialized, the backend explicitly reports that raw resized frames are being used. This may differ from the preprocessing used to train the referenced model and could affect recognition quality.

## Run tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

## Project documents

- [SETUP.md](SETUP.md) — Windows setup and troubleshooting.
- [ARCHITECTURE.md](ARCHITECTURE.md) — components and data flow.
- [TESTING.md](TESTING.md) — test plan and known validation limitations.
- [COMMUNITY_IMPACT.md](COMMUNITY_IMPACT.md) — proposed community validation.
- [PROJECT_REPORT.md](PROJECT_REPORT.md) — academic project overview and methodology.
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) — reference repository and external resource attribution.

## Limitations and responsible use

- Word-level recognition is not full continuous sign-language translation. Sign languages have their own grammar and linguistic structure.
- ISL signs can have regional and contextual variation.
- The current vocabulary practice checks written word recall only; it does not test the correctness of a sign.
- The model endpoint and model weights are external dependencies; the app does not bundle the upstream model weights.
- The PWA prototype does not include Firebase authentication. Its local history and feedback database are not a production multi-user service.
- The app is an educational prototype, not a certified interpreter or an emergency communication service.
- Do not store or process other people's video without informed consent.

## Licence

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The MIT licence and copyright notice of the reference repository are preserved in the third-party notice file.
