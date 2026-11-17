from fastapi.testclient import TestClient
from backend.main import app
from backend import store


def test_health_and_config(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'api.sqlite3')
    with TestClient(app) as client:
        health = client.get('/api/health')
        assert health.status_code == 200
        assert health.json()['app'] == 'SanketSetu'
        config = client.get('/api/config')
        assert config.status_code == 200
        assert config.json()['recognition_clip_frames'] == 16


def test_history_api(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'api-history.sqlite3')
    with TestClient(app) as client:
        created = client.post('/api/history', json={'text':'Good morning','source':'test'})
        assert created.status_code == 201
        item_id = created.json()['id']
        assert client.get('/api/history').json()['items'][0]['text'] == 'Good morning'
        assert client.delete(f'/api/history/{item_id}').status_code == 200


def test_frontend_shell_and_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'frontend.sqlite3')
    with TestClient(app) as client:
        home = client.get('/')
        assert home.status_code == 200
        assert 'SanketSetu' in home.text
        assert 'Live translation' in home.text
        asset = client.get('/assets/app.js')
        assert asset.status_code == 200
        assert 'buildPhraseLookup' in asset.text
        manifest = client.get('/manifest.webmanifest')
        assert manifest.status_code == 200
        assert manifest.json()['short_name'] == 'SanketSetu'
