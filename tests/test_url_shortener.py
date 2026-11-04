import pytest
from app.url_shortener import URLShortener


def test_create_resolve_and_analytics(tmp_path):
    service = URLShortener(str(tmp_path / "nested" / "links.db"))
    created = service.shorten("https://example.com/a/long/path")
    assert created["created"] is True
    assert len(created["code"]) == 7
    assert service.resolve(created["code"]) == "https://example.com/a/long/path"
    assert service.analytics(created["code"])["click_count"] == 1


def test_same_url_is_idempotent(tmp_path):
    service = URLShortener(str(tmp_path / "links.db"))
    first = service.shorten("https://example.com/same")
    second = service.shorten("https://example.com/same")
    assert first["code"] == second["code"]
    assert second["created"] is False


def test_distinct_urls_get_distinct_codes(tmp_path):
    service = URLShortener(str(tmp_path / "links.db"))
    codes = {service.shorten(f"https://example.com/{i}")["code"] for i in range(30)}
    assert len(codes) == 30


def test_rejects_non_http_urls(tmp_path):
    service = URLShortener(str(tmp_path / "links.db"))
    with pytest.raises(ValueError):
        service.shorten("javascript:alert(1)")


def test_list_urls_includes_click_count(tmp_path):
    service = URLShortener(str(tmp_path / "links.db"))
    item = service.shorten("https://example.com/list")
    service.resolve(item["code"])
    rows = service.list_urls()
    assert rows[0]["code"] == item["code"]
    assert rows[0]["click_count"] == 1
