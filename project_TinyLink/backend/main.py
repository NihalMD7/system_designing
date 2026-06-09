"""TinyLink FastAPI app.

Routes:
    GET  /                      -> serve frontend index.html
    POST /api/shorten           -> create short code for a long URL
    GET  /api/links/{code}      -> meta lookup (JSON, no redirect)
    GET  /{code}                -> 302 redirect to long URL
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from .base62 import decode, encode
from .db import connect

RESERVED = {"api", "static", "docs", "redoc", "openapi.json", "favicon.ico"}

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="TinyLink", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

conn = connect()


class ShortenIn(BaseModel):
    long: HttpUrl


class ShortenOut(BaseModel):
    code: str
    short: str
    long: str


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/shorten", response_model=ShortenOut)
def create_short(body: ShortenIn, request: Request) -> ShortenOut:
    long_url = str(body.long)
    cur = conn.execute(
        "INSERT INTO links (long_url) VALUES (?)",
        (long_url,),
    )
    conn.commit()
    code = encode(cur.lastrowid)
    base = str(request.base_url).rstrip("/")
    return ShortenOut(code=code, short=f"{base}/{code}", long=long_url)


@app.get("/api/links/{code}")
def link_meta(code: str) -> dict:
    if code in RESERVED:
        raise HTTPException(404, "not found")
    try:
        link_id = decode(code)
    except ValueError:
        raise HTTPException(400, "invalid code")
    row = conn.execute(
        "SELECT id, long_url, created FROM links WHERE id = ?",
        (link_id,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "not found")
    return {"code": code, "long": row["long_url"], "created": row["created"]}


@app.get("/{code}", include_in_schema=False)
def follow(code: str) -> RedirectResponse:
    if code in RESERVED:
        raise HTTPException(404, "not found")
    try:
        link_id = decode(code)
    except ValueError:
        raise HTTPException(404, "not found")
    row = conn.execute(
        "SELECT long_url FROM links WHERE id = ?",
        (link_id,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "not found")
    return RedirectResponse(row["long_url"], status_code=302)
