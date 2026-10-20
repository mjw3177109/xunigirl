"""VoiceCompanion independent web/API runtime. No DeepSeek Harness requirement.

The DeepSeek API runs remotely; the optional pinned local speech bridge provides
FunASR, Qwen3-TTS, and DUIX. No API keys are returned to the browser or SQLite.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.store import Store

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
WEB = ROOT / "web"
STORE = Store(ROOT / "data" / "conversations.db")
logger = logging.getLogger("voicecompanion")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = FastAPI(title="VoiceCompanion DeepSeek 4090", version="1.1.0")
ALLOWED_MODELS = {"deepseek-flash", "deepseek-v4-pro"}
voice_loaded = False
voice_error = ""


@dataclass
class Turn:
    id: str
    cancelled: bool = False


active_turns: dict[str, Turn] = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=4000)
    model: str = "deepseek-flash"
    system_prompt: str | None = Field(default=None, max_length=2000)


class CancelRequest(BaseModel):
    session_id: str


class MemoryRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500)


def api_key_ready() -> bool:
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    return bool(key) and not any(word in key.lower() for word in ["your", "replace", "请替换", "你的", "example"])


def system_prompt(custom: str | None) -> str:
    fp = ROOT / "config" / "persona.txt"
    base = fp.read_text(encoding="utf-8") if fp.exists() else "你是一位自然、友好的中文语音助手。"
    notes = STORE.memories(40)
    if notes:
        base += "\n用户明确保存的本地偏好或事实（如与本次话题无关不必提及）：\n" + "\n".join(
            "- " + note["content"] for note in reversed(notes)
        )[:5000]
    if custom and custom.strip():
        base += "\n当前会话的额外风格设置：" + custom.strip()
    return base


def sse_event(event: str, **kwargs) -> bytes:
    return ("data: " + json.dumps({"event": event, **kwargs}, ensure_ascii=False) + "\n\n").encode()


def parse_sse_line(line: str) -> str:
    if not line.startswith("data:"):
        return ""
    data = line[5:].strip()
    if not data or data == "[DONE]":
        return ""
    try:
        decoded = json.loads(data)
        return "".join(str((choice.get("delta") or {}).get("content") or "")
                       for choice in decoded.get("choices", []) if isinstance(choice, dict))
    except (TypeError, ValueError, AttributeError):
        return ""


consume_deepseek_line = parse_sse_line


async def stream_deepseek(messages: list[dict], model: str, key: str) -> AsyncIterator[str]:
    base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    endpoint = base if base.endswith("/chat/completions") else base + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "thinking": {"type": "disabled"},
        "max_tokens": int(os.getenv("DEEPSEEK_MAX_TOKENS", "1024")),
    }
    timeout = httpx.Timeout(connect=20, read=150, write=20, pool=20)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        async with client.stream("POST", endpoint, headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        }, json=payload) as response:
            if response.status_code != 200:
                body = (await response.aread()).decode("utf-8", errors="replace")[:350]
                raise RuntimeError(f"DeepSeek API HTTP {response.status_code}: {body}")
            async for line in response.aiter_lines():
                delta = parse_sse_line(line)
                if delta:
                    yield delta


@app.get("/")
async def home():
    return FileResponse(WEB / "index.html")


@app.get("/api/app/status")
async def status():
    return {
        "ok": True, "version": "1.1.0", "api_configured": api_key_ready(),
        "model_default": os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        "voice_loaded": voice_loaded, "voice_error": voice_error,
        "active_chats": len(active_turns),
    }


@app.get("/api/app/gpu")
async def gpu():
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        )
        values = proc.stdout.strip().splitlines()[0].split(",")
        return {"available": True, "name": values[0].strip(), "used_mb": int(values[1]), "total_mb": int(values[2])}
    except (OSError, IndexError, ValueError, subprocess.SubprocessError):
        return {"available": False}


@app.get("/api/app/sessions")
async def get_sessions():
    return {"sessions": STORE.list_sessions()}


@app.post("/api/app/sessions")
async def new_session():
    return {"id": STORE.create()}


@app.get("/api/app/sessions/{session_id}")
async def get_session(session_id: str):
    if not STORE.exists(session_id):
        raise HTTPException(404, "Session not found")
    return {"messages": STORE.list_messages(session_id, limit=500)}


@app.delete("/api/app/sessions/{session_id}")
async def delete_session(session_id: str):
    turn = active_turns.get(session_id)
    if turn:
        turn.cancelled = True
    STORE.delete(session_id)
    return {"ok": True}


@app.get("/api/app/memories")
async def get_memories():
    return {"memories": STORE.memories()}


@app.post("/api/app/memories")
async def add_memory(req: MemoryRequest):
    return {"id": STORE.add_memory(req.content)}


@app.delete("/api/app/memories/{memory_id}")
async def delete_memory(memory_id: int):
    if not STORE.delete_memory(memory_id):
        raise HTTPException(404, "Memory not found")
    return {"ok": True}


@app.post("/api/app/cancel")
async def cancel(req: CancelRequest):
    turn = active_turns.get(req.session_id)
    if turn:
        turn.cancelled = True
    return {"ok": True}


@app.post("/api/app/chat/stream")
async def chat(req: ChatRequest, request: Request):
    if not STORE.exists(req.session_id):
        raise HTTPException(404, "Session not found")
    if req.model not in ALLOWED_MODELS:
        raise HTTPException(422, "Unsupported model")
    if not api_key_ready():
        raise HTTPException(503, "请在项目根目录 .env 中设置 DEEPSEEK_API_KEY")
    if req.session_id in active_turns:
        raise HTTPException(409, "该会话还有正在结束的回复，请停止后重试")

    turn = Turn(str(uuid.uuid4()))
    active_turns[req.session_id] = turn
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()

    async def generate():
        answer: list[str] = []
        completed = False
        try:
            context = STORE.list_messages(req.session_id, limit=24)
            prompt = [{"role": "system", "content": system_prompt(req.system_prompt)}]
            prompt.extend({"role": msg["role"], "content": msg["content"]} for msg in context)
            prompt.append({"role": "user", "content": req.message.strip()})
            STORE.append(req.session_id, "user", req.message.strip())
            yield sse_event("start", turn_id=turn.id)
            async for delta in stream_deepseek(prompt, req.model, key):
                if turn.cancelled or await request.is_disconnected():
                    yield sse_event("cancelled", turn_id=turn.id)
                    return
                answer.append(delta)
                yield sse_event("delta", text=delta)
            if turn.cancelled:
                yield sse_event("cancelled", turn_id=turn.id)
                return
            final = "".join(answer).strip()
            if final:
                STORE.append(req.session_id, "assistant", final)
            completed = True
            yield sse_event("done", text=final)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("DeepSeek stream failed (type=%s)", type(exc).__name__)
            yield sse_event("error", message=str(exc)[:400])
        finally:
            if active_turns.get(req.session_id) is turn:
                active_turns.pop(req.session_id, None)
            if not completed:
                logger.info("Incomplete turn cancelled or failed: %s", turn.id)

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })


UPSTREAM = ROOT / "upstream"
try:
    if (UPSTREAM / "bridge" / "voice_bridge.py").is_file():
        os.chdir(UPSTREAM)
        sys.path.insert(0, str(UPSTREAM / "bridge"))
        import voice_bridge  # type: ignore[import-not-found]
        app.mount("/voice", voice_bridge.app, name="upstream-voice")
        if hasattr(voice_bridge, "_dh_start_worker"):
            app.add_event_handler("startup", voice_bridge._dh_start_worker)
        voice_loaded = True
except Exception as exc:
    voice_error = f"{type(exc).__name__}: {str(exc)[:250]}"
    logger.exception("Optional speech backend failed to mount; text-only mode remains available")

app.mount("/portraits", StaticFiles(directory=ROOT / "assets" / "portraits"), name="character-portraits")
app.mount("/static", StaticFiles(directory=WEB), name="frontend-static")
