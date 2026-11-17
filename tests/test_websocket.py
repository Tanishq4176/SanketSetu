import io
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app, model_client
from backend import store


def make_jpeg():
    buffer = io.BytesIO()
    Image.new('RGB', (40, 40), color=(80, 120, 90)).save(buffer, format='JPEG')
    return buffer.getvalue()


def test_websocket_reports_model_unavailable_without_fake_prediction(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'ws.sqlite3')
    monkeypatch.setattr(model_client, 'base_url', '')
    jpeg = make_jpeg()
    with TestClient(app) as client:
        with client.websocket_connect('/ws/translate') as websocket:
            ready = websocket.receive_json()
            assert ready['type'] == 'ready'
            assert ready['model_configured'] is False
            for _ in range(16):
                websocket.send_bytes(jpeg)
            message = websocket.receive_json()
            assert message['type'] == 'model_unavailable'
            assert 'No prediction has been generated' in message['message']
