# Architecture

Browser -> FastAPI -> URL service -> SQLite repository. Redirect requests resolve a short code and increment click count. Production evolution: PostgreSQL, hot-key cache, async event ingestion, abuse controls and backups.
