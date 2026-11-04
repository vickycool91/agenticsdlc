# URL Shortener

Run from this directory with `uvicorn app.main:app --reload --port 8010`. SQLite-backed demo exposing URL creation, redirects and click analytics.

## URL management and analytics

The generated service exposes `GET /api/urls` to list recently created links and
`GET /api/urls/{code}/analytics` to inspect the redirect count. The Studio-hosted
interactive demo is available from the main workspace at `/demo`; it uses the
same SQLite-backed URL-shortening service, with its own database under this
example's output directory. Short codes are random Base62 values, and repeating
the same URL returns its existing code. Only absolute `http` and `https` URLs
are accepted.
