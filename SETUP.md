# Windows setup

## 1. Requirements

- Windows 10/11
- Python 3.12 recommended (64-bit)
- A current Chrome, Edge or Firefox browser
- Internet connection for installing Python packages and accessing official ISL learning resources
- A webcam for live camera input

The application is a responsive Progressive Web App (PWA). It runs locally in a browser and can be installed from the browser menu. This avoids requiring Android Studio just to run the community-service prototype.

## 2. Start the application

1. Extract the SanketSetu folder.
2. Double-click `start_windows.bat`.
3. Wait for the first-time dependency installation.
4. Open `http://127.0.0.1:8000` in Chrome or Edge if it does not open automatically.

The script creates `.venv` and `.env` if they do not exist.

## 3. Check the backend

Open `http://127.0.0.1:8000/api/health` to confirm the backend is running.

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## 4. Camera permissions

The camera works on `localhost` / `127.0.0.1` in modern browsers. Press **Enable camera** in Live translation and approve the browser prompt. The browser preview is local; camera frames are transmitted only after you press **Start recognition**.

Use a well-lit room, place the camera at hand/upper-body height, and avoid recording other people without their consent.

## 5. Connect AI inference

There are two supported modes. **Gemini mode is an experimental visual-gesture demo, not a validated ISL translator.**

### Option A — Gemini API key (quick prototype)

1. Open `.env` in a text editor.
2. Add your key as `GEMINI_API_KEY=your_key`.
3. Keep `MODEL_API_BASE_URL=` blank unless you also have a compatible dedicated ISL service.
4. Optionally set `GEMINI_MODEL=gemini-2.5-flash-lite`.
5. Save and restart `start_windows.bat`.
6. Open `http://127.0.0.1:8000/api/config`; the provider should show `gemini_experimental`.

Gemini analyses a batch of 16 selected camera frames and returns a best-effort visual guess. It may misunderstand ISL, movement, grammar or context. The app does not display a calibrated confidence score in this mode. Gemini free-tier availability and limits depend on your Google AI Studio project and current quotas. Review Google's data-use terms before sending anyone's camera images.

### Option B — Dedicated ISL inference service

Set `MODEL_API_BASE_URL` to the base URL of a service exposing the compatible `POST /predict_frames_bin` endpoint. This option takes precedence over Gemini. A model-card URL is not itself an inference endpoint.

The server sends 16 JPEG frames in the ISLF binary container and expects JSON containing `prediction` or `label`, and optionally `confidence`. See `model/README.md`.

## 6. Optional MediaPipe landmark preprocessing

SanketSetu optionally supports MediaPipe hand and pose landmark overlays, which requires separate `.task` assets.

In a second activated terminal:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-vision.txt
python -m backend.download_vision_models
```

Restart the server. The WebSocket `ready` message and the Live translation status will indicate whether MediaPipe initialized. If the dependency or model files are missing, the backend falls back to raw resized frames and reports that limitation. Recognition accuracy must not be assumed equivalent to the original preprocessing pipeline.

MediaPipe package compatibility can vary by Python version and operating system. Use Python 3.12 if installation fails with Python 3.13.

## 7. Stop the server

Focus the terminal window and press `Ctrl+C`.

## 8. Mobile use on the same Wi-Fi network

For an Android phone to access the development PC:

1. Find the PC's local IPv4 address using `ipconfig`.
2. Start Uvicorn using `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
3. Allow Python through the Windows Firewall on a private network.
4. On the phone, open `http://PC_IPV4_ADDRESS:8000`.

Most browsers require HTTPS for camera access on a remote LAN IP. For mobile camera testing, use a trusted HTTPS tunnel or a properly configured local HTTPS certificate. Do not expose the development server to public networks.

## Troubleshooting

- **`py -3.12` not found:** install Python 3.12 x64 and enable the Python launcher.
- **Port 8000 is busy:** run `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001` and open port 8001.
- **Camera permission blocked:** use `http://127.0.0.1:8000`, allow camera in browser site settings and reload.
- **AI model not connected:** check `.env`, model endpoint path and server logs. Do not use the demo preview as model evidence.
- **MediaPipe missing:** the main app remains usable; install the optional vision requirements and download the task assets if required.
