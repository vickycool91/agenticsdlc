import pytest
from app.url_shortener import URLShortener

def test_shorten_resolve_and_analytics(tmp_path):
    service=URLShortener(str(tmp_path/"urls.db")); item=service.shorten("https://example.com/path")
    assert item["code"] and service.resolve(item["code"])=="https://example.com/path"
    assert service.analytics(item["code"])["click_count"]==1

def test_same_url_is_idempotent(tmp_path):
    service=URLShortener(str(tmp_path/"urls.db")); first=service.shorten("https://example.com")
    second=service.shorten("https://example.com")
    assert first["code"]==second["code"]

def test_rejects_invalid_url(tmp_path):
    service=URLShortener(str(tmp_path/"urls.db"))
    with pytest.raises(ValueError): service.shorten("javascript:alert(1)")

def test_unknown_code(tmp_path):
    service=URLShortener(str(tmp_path/"urls.db"))
    assert service.resolve("missing") is None and service.analytics("missing") is None
