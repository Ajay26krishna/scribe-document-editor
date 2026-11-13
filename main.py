"""Scribe API: product-scope demo authentication, ownership & sharing, persisted rich text."""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from importer import to_delta
from storage import Storage, initialize

HERE = Path(__file__).resolve().parent
MAX_UPLOAD = 512 * 1024
MAX_DELTA = 250_000
ALLOWED_ATTRS = {
    "bold": (True,), "italic": (True,), "underline": (True,), "strike": (True,),
    "code": (True,), "blockquote": (True,), "header": (1, 2, 3),
    "list": ("bullet", "ordered"), "align": ("left", "center", "right"),
}


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_title(value: str) -> str:
    title = " ".join(value.split())
    if not 1 <= len(title) <= 120:
        raise HTTPException(422, "Document title must be 1–120 characters")
    return title


def validate_delta(delta: dict) -> str:
    if not isinstance(delta, dict) or set(delta) != {"ops"} or not isinstance(delta["ops"], list):
        raise HTTPException(422, "Invalid editor content")
    ops = delta["ops"]
    if not 1 <= len(ops) <= 5000:
        raise HTTPException(422, "Document content requires 1–5000 operations")
    if any(not isinstance(op, dict) or "insert" not in op or not isinstance(op["insert"], str)
           or set(op) - {"insert", "attributes"} for op in ops):
        raise HTTPException(422, "Only text formatting is supported")
    for op in ops:
        attrs = op.get("attributes", {})
        if not isinstance(attrs, dict):
            raise HTTPException(422, "Invalid formatting attributes")
        for key, value in attrs.items():
            # type-sensitive comparison prevents 1 being accepted as True and vice versa.
            if key not in ALLOWED_ATTRS or not any(value == item and type(value) is type(item) for item in ALLOWED_ATTRS[key]):
                raise HTTPException(422, "Unsupported text formatting")
    if sum(len(op["insert"]) for op in ops) > 100_000:
        raise HTTPException(413, "Document exceeds the 100,000 character limit")
    encoded = json.dumps(delta, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_DELTA:
        raise HTTPException(413, "Document exceeds the 250 KB limit")
    return encoded


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = Storage()
    initialize(app.state.db)
    yield


app = FastAPI(title="Scribe API", version="1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")


@app.middleware("http")
async def headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def db(request: Request) -> Storage:
    return request.app.state.db


def current_user(request: Request) -> dict:
    user_id = request.cookies.get("scribe_demo_user", "maya")
    return db(request).one("SELECT * FROM users WHERE id=?", user_id) or db(request).one("SELECT * FROM users WHERE id=?", "maya")


def access_doc(request: Request, doc_id: str) -> dict:
    user = current_user(request)
    result = db(request).one("""
        SELECT d.*, u.name AS owner_name, u.email AS owner_email, s.role AS share_role
        FROM documents d JOIN users u ON u.id = d.owner_id
        LEFT JOIN shares s ON s.doc_id = d.id AND s.user_id = ?
        WHERE d.id = ? AND (d.owner_id = ? OR s.user_id IS NOT NULL)
    """, user["id"], doc_id, user["id"])
    if not result:
        raise HTTPException(404, "Document not found or not shared with this account")
    result["role"] = "owner" if result["owner_id"] == user["id"] else result["share_role"]
    result.pop("share_role", None)
    return result


def owner_doc(request: Request, doc_id: str) -> dict:
    item = access_doc(request, doc_id)
    if item["role"] != "owner":
        raise HTTPException(403, "Only the owner can manage sharing or delete this document")
    return item


def present_doc(item: dict, include_content: bool = False) -> dict:
    selected = {k: item[k] for k in ("id", "owner_id", "owner_name", "owner_email", "title", "revision", "created_at", "updated_at", "role")}
    if include_content:
        selected["delta"] = json.loads(item["delta_json"])
    return selected


class SessionChoice(BaseModel):
    user_id: Literal["maya", "noah"]


@app.get("/api/session")
def get_session(request: Request):
    return {"current": current_user(request), "users": db(request).all("SELECT * FROM users ORDER BY name")}


@app.post("/api/session")
def set_session(payload: SessionChoice, request: Request, response: Response):
    user = db(request).one("SELECT * FROM users WHERE id=?", payload.user_id)
    if not user:
        raise HTTPException(404, "Unknown demo user")
    # Demo identity switching is intentional, not a production sign-in flow.
    secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie("scribe_demo_user", user["id"], httponly=True, samesite="strict", secure=secure, max_age=604800)
    return {"current": user}


@app.get("/api/documents")
def list_documents(request: Request):
    user = current_user(request)
    rows = db(request).all("""
        SELECT d.*, u.name AS owner_name, u.email AS owner_email, s.role AS share_role
        FROM documents d JOIN users u ON u.id = d.owner_id
        LEFT JOIN shares s ON s.doc_id = d.id AND s.user_id = ?
        WHERE d.owner_id = ? OR s.user_id IS NOT NULL
        ORDER BY d.updated_at DESC
    """, user["id"], user["id"])
    for item in rows:
        item["role"] = "owner" if item["owner_id"] == user["id"] else item["share_role"]
    return {"documents": [present_doc(x) for x in rows]}


class CreateDocument(BaseModel):
    title: str = "Untitled document"


@app.post("/api/documents", status_code=201)
def create_document(payload: CreateDocument, request: Request):
    user = current_user(request)
    doc_id, now = str(uuid4()), timestamp()
    db(request).change("INSERT INTO documents(id,owner_id,title,delta_json,revision,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                       doc_id, user["id"], validate_title(payload.title), json.dumps({"ops": [{"insert": "\n"}]}), 1, now, now)
    return {"document": present_doc(access_doc(request, doc_id), include_content=True)}


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, request: Request):
    return {"document": present_doc(access_doc(request, doc_id), include_content=True)}


class UpdateDocument(BaseModel):
    revision: int = Field(ge=1)
    title: str | None = None
    delta: dict | None = None


@app.patch("/api/documents/{doc_id}")
def update_document(doc_id: str, payload: UpdateDocument, request: Request):
    item = access_doc(request, doc_id)
    if item["role"] == "viewer":
        raise HTTPException(403, "Viewers cannot edit documents")
    if payload.title is None and payload.delta is None:
        raise HTTPException(422, "Provide a title or document content")
    title = validate_title(payload.title) if payload.title is not None else item["title"]
    content = validate_delta(payload.delta) if payload.delta is not None else item["delta_json"]
    changed = db(request).change("""
        UPDATE documents SET title=?, delta_json=?, revision=revision+1, updated_at=?
        WHERE id=? AND revision=?
    """, title, content, timestamp(), doc_id, payload.revision)
    if changed == 0:
        raise HTTPException(409, "This document was updated elsewhere. Reopen it to load the latest version.")
    return {"document": present_doc(access_doc(request, doc_id))}


@app.delete("/api/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str, request: Request):
    owner_doc(request, doc_id)
    db(request).change("DELETE FROM shares WHERE doc_id=?", doc_id)
    db(request).change("DELETE FROM documents WHERE id=?", doc_id)
    return Response(status_code=204)


@app.get("/api/documents/{doc_id}/shares")
def list_shares(doc_id: str, request: Request):
    owner_doc(request, doc_id)
    rows = db(request).all("""
        SELECT u.id AS user_id, u.name, u.email, s.role
        FROM shares s JOIN users u ON u.id = s.user_id
        WHERE s.doc_id=? ORDER BY u.name
    """, doc_id)
    return {"shares": rows}


class ShareUser(BaseModel):
    email: str
    role: Literal["viewer", "editor"] = "editor"


@app.post("/api/documents/{doc_id}/shares")
def share_document(doc_id: str, payload: ShareUser, request: Request):
    item = owner_doc(request, doc_id)
    email = payload.email.strip().lower()
    user = db(request).one("SELECT * FROM users WHERE lower(email)=?", email)
    if not user:
        raise HTTPException(404, "User not found. Use one of the two seeded demo accounts.")
    if user["id"] == item["owner_id"]:
        raise HTTPException(422, "The owner already has full access")
    db(request).change("""
        INSERT INTO shares(doc_id,user_id,role) VALUES(?,?,?)
        ON CONFLICT(doc_id,user_id) DO UPDATE SET role=excluded.role
    """, doc_id, user["id"], payload.role)
    return {"shared_with": {"user_id": user["id"], "name": user["name"], "email": user["email"], "role": payload.role}}


@app.delete("/api/documents/{doc_id}/shares/{user_id}", status_code=204)
def revoke_share(doc_id: str, user_id: str, request: Request):
    owner_doc(request, doc_id)
    db(request).change("DELETE FROM shares WHERE doc_id=? AND user_id=?", doc_id, user_id)
    return Response(status_code=204)


@app.post("/api/import", status_code=201)
async def import_document(request: Request, file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in (".txt", ".md"):
        raise HTTPException(422, "Only .txt and .md files are supported")
    contents = await file.read(MAX_UPLOAD + 1)
    if len(contents) > MAX_UPLOAD:
        raise HTTPException(413, "Maximum upload size is 512 KB")
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(422, "File must be UTF-8 encoded") from exc
    delta = to_delta(text, suffix)
    encoded = validate_delta(delta)
    title = validate_title(Path(filename).stem)
    user = current_user(request)
    doc_id, now = str(uuid4()), timestamp()
    db(request).change("INSERT INTO documents(id,owner_id,title,delta_json,revision,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                       doc_id, user["id"], title, encoded, 1, now, now)
    return {"document": present_doc(access_doc(request, doc_id), include_content=True)}


@app.get("/healthz")
def healthz(request: Request):
    db(request).one("SELECT id FROM users LIMIT 1")
    return {"status": "ok", "storage": "turso" if db(request).remote_url else "sqlite"}


@app.get("/")
def home():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/docs/{doc_id}")
def doc_page(doc_id: str):
    return FileResponse(HERE / "static" / "index.html")
