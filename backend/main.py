import os
import io
import json
import zipfile
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

BRAND = "Fans of the One"
API_KEY_ENV = "FANS_OF_THE_ONE_API_KEY"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(String, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    raw_input = Column(Text, nullable=False)
    structured_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)

class DownloadToken(Base):
    __tablename__ = "download_tokens"
    token = Column(String, primary_key=True, index=True)
    artifact_id = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)

def init_db():
    # For local dev only. In production, use alembic migrations.
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_api_key(x_api_key: str | None = Header(default=None)):
    expected = os.getenv(API_KEY_ENV)
    if not expected:
        return True
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

class ConvertPayload(BaseModel):
    raw_input: str = Field(..., min_length=1, max_length=20000)
    mode: str = Field(..., min_length=1, max_length=64)

app = FastAPI(title=f"{BRAND} Engine", version="1.2.0")

@app.on_event("startup")
def _startup():
    # Local dev safety. On Railway, run alembic via scripts.
    if os.getenv("AUTO_CREATE_TABLES", "0") == "1":
        init_db()

@app.get("/health")
def health():
    return {"status": "ok", "brand": BRAND, "version": "1.2.0"}

@app.post("/engine/convert")
def convert(payload: ConvertPayload, _: bool = Depends(require_api_key), db: Session = Depends(get_db)):
    artifact_id = str(uuid4())
    structured = {
        "brand": BRAND,
        "mode": payload.mode,
        "summary": payload.raw_input[:200],
        "constraints": [],
        "assumptions": [],
        "execution_plan": [
            "Clarify intent into one sentence",
            "List hard constraints (time, money, tools)",
            "Break into 3–7 executable steps",
            "Export plan as zip (md + json)"
        ],
    }
    row = Artifact(
        id=artifact_id,
        brand=BRAND,
        mode=payload.mode,
        raw_input=payload.raw_input,
        structured_json=json.dumps(structured, ensure_ascii=False, indent=2),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return {"id": artifact_id, "brand": BRAND, "structured_output": structured}

@app.get("/engine/artifacts/{artifact_id}")
def get_artifact(artifact_id: str, _: bool = Depends(require_api_key), db: Session = Depends(get_db)):
    row = db.get(Artifact, artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": row.id,
        "brand": row.brand,
        "mode": row.mode,
        "raw_input": row.raw_input,
        "structured_output": json.loads(row.structured_json),
        "created_at": row.created_at.isoformat() + "Z",
    }

def _artifact_zip_bytes(row: Artifact) -> io.BytesIO:
    structured = json.loads(row.structured_json)
    md = f"""# {BRAND} Artifact

**Artifact ID:** {row.id}
**Mode:** {row.mode}
**Created:** {row.created_at.isoformat()}Z

## Summary
{structured.get("summary","")}

## Execution Plan
""" + "\n".join([f"- {s}" for s in structured.get("execution_plan", [])]) + f"""

## Raw Input (truncated)
```
{row.raw_input[:2000]}
```
"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("artifact.json", json.dumps({
            "id": row.id,
            "brand": row.brand,
            "mode": row.mode,
            "raw_input": row.raw_input,
            "structured_output": structured,
            "created_at": row.created_at.isoformat() + "Z",
        }, ensure_ascii=False, indent=2))
        z.writestr("artifact.md", md)
    buf.seek(0)
    return buf

@app.get("/engine/artifacts/{artifact_id}/export")
def export_artifact_zip(artifact_id: str, _: bool = Depends(require_api_key), db: Session = Depends(get_db)):
    row = db.get(Artifact, artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    buf = _artifact_zip_bytes(row)
    filename = f"{BRAND.lower().replace(' ', '_')}_artifact_{row.id}.zip"
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

class TokenReq(BaseModel):
    artifact_id: str = Field(..., min_length=1)
    ttl_seconds: int = Field(300, ge=30, le=3600)

@app.post("/engine/export-token")
def create_export_token(req: TokenReq, _: bool = Depends(require_api_key), db: Session = Depends(get_db)):
    # Create a one-time download token so a browser can download without headers.
    row = db.get(Artifact, req.artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    token = str(uuid4())
    now = datetime.utcnow()
    tok = DownloadToken(
        token=token,
        artifact_id=req.artifact_id,
        created_at=now,
        expires_at=now + timedelta(seconds=req.ttl_seconds),
    )
    db.add(tok)
    db.commit()
    return {"token": token, "expires_at": tok.expires_at.isoformat() + "Z"}

@app.get("/engine/download/{token}")
def download_with_token(token: str, db: Session = Depends(get_db)):
    tok = db.get(DownloadToken, token)
    if not tok:
        raise HTTPException(status_code=404, detail="Invalid token")
    if tok.expires_at < datetime.utcnow():
        # burn expired token
        db.delete(tok)
        db.commit()
        raise HTTPException(status_code=410, detail="Token expired")
    row = db.get(Artifact, tok.artifact_id)
    if not row:
        db.delete(tok)
        db.commit()
        raise HTTPException(status_code=404, detail="Not found")
    # burn token after use (single-use)
    db.delete(tok)
    db.commit()
    buf = _artifact_zip_bytes(row)
    filename = f"{BRAND.lower().replace(' ', '_')}_artifact_{row.id}.zip"
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
