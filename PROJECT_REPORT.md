# SanketSetu — Community Service Project Report

## 1. Abstract

SanketSetu is a student-developed accessibility prototype focused on Indian Sign Language learning and technology-assisted communication. It brings trusted ISL learning links, beginner vocabulary recall, a camera-based recognition interface, sentence composition, speech output, local history and community feedback into one simple application. The software uses a responsive Progressive Web App frontend and a FastAPI backend. Its recognition interface is designed to connect to a separate 16-frame ISL inference service. Real recognition is explicitly reported as unavailable until that external model service is configured and validated.

## 2. Problem statement

People who use Indian Sign Language may encounter communication barriers when interacting with people who have not learned ISL. Hearing community members may also find it difficult to locate reliable sign-language demonstrations or practise vocabulary. A student-built prototype can provide a learning entry point and demonstrate a possible technical recognition workflow, while respecting the linguistic and cultural expertise of Deaf people and qualified ISL educators.

## 3. Objectives

1. Provide an accessible interface for exploring reliable ISL learning material.
2. Offer a beginner vocabulary recall activity.
3. Build a camera-streaming interface that can communicate with a separately hosted ISL word-recognition model.
4. Provide sentence composition, browser speech output and user-controlled local history.
5. Document technical limitations and use community feedback to guide future improvements.

## 4. Scope

The first implementation includes a responsive PWA, FastAPI routes, WebSocket frame streaming, an ISLF-compatible binary frame packer, optional MediaPipe landmark processing, a model API adapter, SQLite storage and automated backend tests. It does not claim full sentence-level ISL translation, certified interpretation, a bundled model server, multi-user authentication or an evaluated production deployment.

## 5. System design

The browser requests camera permission only after the user presses Enable camera. Recognition frames are sent only after Start recognition. Frames travel over a WebSocket to the FastAPI backend. The backend validates JPEG data, optionally applies pose and hand landmark overlays, resizes the frame and assembles a 16-frame overlapping clip. The model adapter packages the clip using the ISLF binary format and posts it to a configured external inference service. Returned labels are shown in the browser and can be added to a user-edited sentence. Users can speak or save the sentence.

The frontend also exposes a vocabulary library, practice activity and official ISL learning links. History and feedback are stored in a local SQLite database. Camera images are not saved by this project.

## 6. Technology stack

- HTML, CSS and JavaScript for the responsive PWA.
- FastAPI and Uvicorn for REST and WebSocket APIs.
- Pillow for image handling.
- Optional MediaPipe Tasks and OpenCV for landmark overlays.
- Python `requests` for remote model-service calls.
- SQLite for local persistence.
- Browser Speech Synthesis for voice output.
- pytest and FastAPI TestClient for automated backend tests.

## 7. Project implementation and design choices

SanketSetu is built as a responsive Progressive Web App with dedicated navigation and layout, a vocabulary learning space, a practice recall activity, local history/feedback services, an explicit model adapter supporting both dedicated model servers and the Gemini API, Windows-first setup scripts, and automated test coverage.

## 8. Testing approach

Automated tests cover ISLF format validation, SQLite storage operations, API health/config and history routes. Manual testing should cover browser camera permissions, WebSocket streaming, real external-model integration, user interface accessibility and community usability. Automated backend tests do not establish AI recognition accuracy.

## 9. Limitations

- Recognition depends on an external service and compatible trained model weights.
- Optional MediaPipe assets and dependencies must be installed separately.
- Raw-frame fallback may not match the model's training preprocessing.
- The prototype is intended for word-level recognition; it is not complete sentence-level translation.
- ISL includes grammar, non-manual expression and regional variation that a small word classifier cannot fully capture.
- The local SQLite prototype does not provide production multi-user accounts or cloud backup.

## 10. Future work

1. Deploy and validate the actual model service and reproduce training-time preprocessing.
2. Add signer-diverse evaluation with consent and a documented test protocol.
3. Review vocabulary and visual learning material with Deaf ISL users/educators.
4. Add accessible onboarding and language preferences based on user testing.
5. Consider secure per-user accounts and remote history only after a clear data-protection design.
6. Explore sentence-level temporal modelling as a separate research objective.

## 11. Conclusion

SanketSetu provides a usable learning and accessibility prototype and a documented technical path for real-time ISL recognition integration. Its main contribution is the combination of an accessible learning workflow, a transparent model-service boundary, user-controlled messaging tools and a community validation plan. The application does not overstate recognition capability while the external model runtime remains unconfigured.
