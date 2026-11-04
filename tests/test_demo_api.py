from fastapi.testclient import TestClient
from app.main import app, engine


def unlock_demo(monkeypatch):
    monkeypatch.setitem(engine.runs, "test-approved-run", {
        "run_id": "test-approved-run",
        "approval": {"status": "approved", "decision": True},
    })


def test_demo_is_locked_until_an_engineering_run_is_approved(monkeypatch):
    monkeypatch.setattr(engine, "runs", {})
    client = TestClient(app)
    assert client.get('/demo').status_code == 403
    assert client.get('/demo/api/urls').status_code == 403
    unlock_demo(monkeypatch)
    assert client.get('/demo').status_code == 200
    assert client.get('/demo/api/urls').status_code == 200


def test_demo_shortening_redirect_and_analytics(monkeypatch):
    unlock_demo(monkeypatch)
    client = TestClient(app)
    created = client.post('/demo/api/urls', json={'url': 'https://example.org/a/really/long/path'})
    assert created.status_code == 201, created.text
    code = created.json()['code']
    assert created.json()['short_url'] == f'/demo/{code}'

    listed = client.get('/demo/api/urls')
    assert listed.status_code == 200
    assert any(row['code'] == code for row in listed.json())

    redirected = client.get(f'/demo/{code}', follow_redirects=False)
    assert redirected.status_code in (302, 307, 308)
    assert redirected.headers['location'] == 'https://example.org/a/really/long/path'

    analytics = client.get(f'/demo/api/urls/{code}/analytics')
    assert analytics.status_code == 200
    assert analytics.json()['click_count'] == 1


def test_demo_rejects_invalid_scheme(monkeypatch):
    unlock_demo(monkeypatch)
    response = TestClient(app).post('/demo/api/urls', json={'url': 'ftp://example.org/file'})
    assert response.status_code == 422


def test_demo_inline_javascript_keeps_newlines_escaped(monkeypatch):
    unlock_demo(monkeypatch)
    page = TestClient(app).get('/demo').text
    # The HTML is built from a Python triple-quoted string; JS newline escapes
    # must survive as backslash-n rather than becoming literal line breaks.
    assert "alert('Code: '+d.code+'\\nClicks: '+d.click_count+'\\nOriginal URL: '+d.original_url)" in page
