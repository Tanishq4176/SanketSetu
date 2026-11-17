from backend import store


def test_history_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'test.sqlite3')
    store.init_db()
    saved = store.save_history('Hello there', 0.87, 'live')
    assert saved['text'] == 'Hello there'
    assert saved['confidence'] == 0.87
    assert len(store.get_history()) == 1
    assert store.delete_history(saved['id']) is True
    assert store.get_history() == []


def test_feedback_is_stored(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'feedback.sqlite3')
    store.init_db()
    saved = store.save_feedback(5, 'Easy to understand')
    assert saved['rating'] == 5
    assert saved['id'] > 0
