# Testing and validation

## Automated tests

Activate the virtual environment, install the development tools and run:

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

Current test files:

- `tests/test_frame_codec.py` — ISLF packing/unpacking and malformed payloads.
- `tests/test_store.py` — SQLite history and feedback persistence.
- `tests/test_api.py` — health/config and history API integration.

## Manual smoke test

1. Start the backend and open `http://127.0.0.1:8000`.
2. Confirm the Overview page loads and shows model status.
3. Open Learn ISL; search for `water`; open the official dictionary link.
4. Open Practice; finish a five-question round and restart it.
5. Open Live translation; enable the camera and verify the preview.
6. Start recognition. If no model service is configured, confirm the UI explicitly says no prediction was generated.
7. Click **Preview a sample · demo only** and verify that the UI labels it as simulated, without a confidence score.
8. Edit the sentence, use browser speech, copy it and save it.
9. Open History; verify the saved message, delete it and clear history.
10. Submit a test feedback message, then clear the test database if necessary.
11. Stop the server and restart it; confirm saved SQLite messages persist.

## Model integration tests

Only run these after configuring a real compatible inference endpoint.

- Check `/api/config` and inspect `model.status`.
- Confirm the WebSocket `ready` event reports the expected MediaPipe status.
- Start camera streaming and inspect server logs for frame processing and model API responses.
- Confirm a real `prediction` event is returned by the model API, with a label and optional confidence.
- Record latency, confidence and correctness for a labelled test set; include model/service versions and preprocessing conditions.
- Test different lighting, backgrounds, hand sizes, camera angles and signers with consent.

## Results discipline

The automated tests do not verify semantic sign recognition. They validate backend routes, database behaviour and binary frame serialization. No top-1 accuracy, F1 score, signer-independent generalization or real-world translation-quality claim is made by these tests.

Do not use the demo sample or practice quiz score as evidence of AI recognition accuracy.

## Known environment limits

- The authoring container did not have Flutter or MediaPipe installed. The delivered project intentionally uses a browser PWA and makes MediaPipe optional.
- Hardware camera tests require a physical webcam/browser permission and cannot be certified by unit tests.
- The external model service is not bundled; model inference remains an integration test until a real compatible service URL and model server are provided.
