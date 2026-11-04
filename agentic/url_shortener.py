from __future__ import annotations
import hashlib, sqlite3, time
from urllib.parse import urlparse

SCHEMA = """CREATE TABLE IF NOT EXISTS urls (code TEXT PRIMARY KEY, original_url TEXT NOT NULL, created_at REAL NOT NULL, click_count INTEGER NOT NULL DEFAULT 0);"""
class URLShortener:
    def __init__(self, db_path: str = "url_shortener.db", code_length: int = 7):
        self.db_path, self.code_length = db_path, code_length
        with self._connect() as conn: conn.executescript(SCHEMA)
    def _connect(self):
        conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row; return conn
    @staticmethod
    def validate_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc: raise ValueError("url must be an absolute http or https URL")
        return url
    def shorten(self, url: str) -> dict:
        url = self.validate_url(url); digest = hashlib.sha256(url.encode()).hexdigest()
        for extra in range(8):
            code = (digest + (str(extra) if extra else ""))[:self.code_length]
            with self._connect() as conn:
                existing = conn.execute("SELECT code, original_url FROM urls WHERE code=?", (code,)).fetchone()
                if existing and existing["original_url"] == url: return {"code": code, "url": url, "created": False}
                if existing: continue
                try:
                    conn.execute("INSERT INTO urls(code, original_url, created_at) VALUES(?,?,?)", (code, url, time.time()))
                    return {"code": code, "url": url, "created": True}
                except sqlite3.IntegrityError: continue
        raise RuntimeError("unable to allocate unique short code")
    def resolve(self, code: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT original_url FROM urls WHERE code=?", (code,)).fetchone()
            if row is None: return None
            conn.execute("UPDATE urls SET click_count=click_count+1 WHERE code=?", (code,))
            return str(row["original_url"])
    def analytics(self, code: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT code, original_url, created_at, click_count FROM urls WHERE code=?", (code,)).fetchone()
            return dict(row) if row else None
