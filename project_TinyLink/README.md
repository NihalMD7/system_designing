# TinyLink — URL Shortener

Tiny URL shortener: FastAPI + SQLite + Base62. Vanilla HTML/CSS/JS frontend.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Open `http://localhost:8000`.

## Run with Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest -v
```

## Layout

```
backend/
  base62.py    # encode/decode
  db.py        # SQLite connect + schema
  main.py      # FastAPI routes
frontend/
  index.html   # markup
  style.css    # styling
  app.js       # browser logic + fetch
tests/
  test_base62.py
  test_api.py
```

## Endpoints

| Method | Path                  | Purpose                       |
| ------ | --------------------- | ----------------------------- |
| GET    | `/`                   | serve frontend                |
| POST   | `/api/shorten`        | create short code             |
| GET    | `/api/links/{code}`   | meta (JSON)                   |
| GET    | `/{code}`             | 302 redirect to long URL      |
| GET    | `/docs`               | Swagger UI                    |

See `project-explained.html` for line-by-line walkthrough of every file.
