from __future__ import annotations

import asyncio
import json
import re
import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.security import static_dir, verify_password, verify_runtime_file

app = FastAPI(
    title="GPUFlow Local Lab",
    description="A local-network prototype for device messaging and simulated AI workload routing.",
    version="0.1.0",
)

# Prototype state is intentionally in-memory. Restarting the server clears rooms and tokens.
rooms: dict[str, dict[str, WebSocket]] = {}
room_names: dict[str, dict[str, str]] = {}
active_tokens: dict[str, float] = {}
state_lock = asyncio.Lock()
TOKEN_TTL_SECONDS = 8 * 60 * 60
MAX_MESSAGE_LENGTH = 1200
MAX_PROMPT_LENGTH = 4000


class UnlockRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


def clean_room(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", value.strip())[:32]
    return cleaned or "gpuflow-lab"


def clean_name(value: str) -> str:
    cleaned = re.sub(r"[<>\r\n]", "", value.strip())[:24]
    return cleaned or "Device"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def decide_route(prompt: str, requested_mode: str = "auto") -> dict[str, str]:
    """A transparent heuristic demo. It does not call an AI model or allocate a real GPU."""
    mode = requested_mode if requested_mode in {"auto", "light", "balanced", "advanced"} else "auto"
    lowered = prompt.lower()
    demanding_terms = (
        "architecture", "research", "debug", "reason", "analysis", "دقیق", "تحلیل",
        "معماری", "برنامه نویسی", "کدنویسی", "مقایسه", "طراحی سیستم",
    )
    if mode == "light":
        tier, reason = "Lightweight", "Manual selection: lightweight profile"
    elif mode == "balanced":
        tier, reason = "Balanced", "Manual selection: balanced profile"
    elif mode == "advanced":
        tier, reason = "Advanced", "Manual selection: advanced profile"
    else:
        word_count = len(prompt.split())
        if len(prompt) > 850 or word_count > 120 or any(term in lowered for term in demanding_terms):
            tier, reason = "Advanced", "The prompt appears to need more context or deeper reasoning"
        elif len(prompt) > 220 or word_count > 35:
            tier, reason = "Balanced", "The prompt has moderate length or context requirements"
        else:
            tier, reason = "Lightweight", "The prompt appears suitable for a simple workload"
    return {
        "tier": tier,
        "reason": reason,
        "mode": "Heuristic simulation",
        "notice": "Demo decision only — no real model or GPU is selected.",
    }


async def room_snapshot(room: str) -> list[dict[str, str]]:
    async with state_lock:
        names = room_names.get(room, {})
        return [{"id": client_id, "name": name} for client_id, name in names.items()]


async def broadcast(room: str, event: dict[str, Any]) -> None:
    async with state_lock:
        connections = list(rooms.get(room, {}).items())
    dead: list[str] = []
    for client_id, socket in connections:
        try:
            await socket.send_json(event)
        except Exception:
            dead.append(client_id)
    if dead:
        async with state_lock:
            for client_id in dead:
                rooms.get(room, {}).pop(client_id, None)
                room_names.get(room, {}).pop(client_id, None)


@app.on_event("startup")
async def require_companion_file() -> None:
    ok, message = verify_runtime_file()
    if not ok:
        raise RuntimeError(f"GPUFlow cannot start: {message}. Place the supplied companion file beside the launcher.")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(static_dir() / "index.html")


app.mount("/assets", StaticFiles(directory=static_dir()), name="assets")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "product": "GPUFlow Local Lab", "version": "0.1.0", "mode": "local prototype"}


@app.post("/api/unlock")
async def unlock(body: UnlockRequest) -> dict[str, str]:
    if not verify_password(body.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = secrets.token_urlsafe(32)
    active_tokens[token] = time.time() + TOKEN_TTL_SECONDS
    return {"token": token, "expires_in": str(TOKEN_TTL_SECONDS)}


@app.websocket("/ws")
async def websocket_bridge(
    websocket: WebSocket,
    room: str = Query(default="gpuflow-lab", max_length=48),
    name: str = Query(default="Device", max_length=48),
    token: str = Query(default="", max_length=128),
) -> None:
    expiry = active_tokens.get(token)
    if not expiry or expiry < time.time():
        await websocket.close(code=4401, reason="Unlock required")
        return

    room_id = clean_room(room)
    display_name = clean_name(name)
    client_id = str(uuid.uuid4())[:8]
    await websocket.accept()

    async with state_lock:
        rooms.setdefault(room_id, {})[client_id] = websocket
        room_names.setdefault(room_id, {})[client_id] = display_name

    await websocket.send_json({
        "type": "welcome",
        "client_id": client_id,
        "room": room_id,
        "name": display_name,
        "server_time": now_iso(),
    })
    await broadcast(room_id, {"type": "presence", "members": await room_snapshot(room_id)})
    await broadcast(room_id, {"type": "system", "text": f"{display_name} joined the room", "server_time": now_iso()})

    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw) > MAX_PROMPT_LENGTH + 1000:
                await websocket.send_json({"type": "error", "text": "Message is too large"})
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "text": "Invalid message format"})
                continue

            kind = payload.get("type")
            if kind == "chat":
                text = str(payload.get("text", "")).strip()
                if not text:
                    continue
                if len(text) > MAX_MESSAGE_LENGTH:
                    await websocket.send_json({"type": "error", "text": f"Messages are limited to {MAX_MESSAGE_LENGTH} characters"})
                    continue
                await broadcast(room_id, {
                    "type": "chat",
                    "id": str(uuid.uuid4()),
                    "from": display_name,
                    "client_id": client_id,
                    "text": text,
                    "server_time": now_iso(),
                })
            elif kind == "route":
                prompt = str(payload.get("text", "")).strip()
                mode = str(payload.get("mode", "auto"))
                if not prompt:
                    continue
                if len(prompt) > MAX_PROMPT_LENGTH:
                    await websocket.send_json({"type": "error", "text": f"Requests are limited to {MAX_PROMPT_LENGTH} characters"})
                    continue
                result = decide_route(prompt, mode)
                await broadcast(room_id, {
                    "type": "route",
                    "id": str(uuid.uuid4()),
                    "from": display_name,
                    "client_id": client_id,
                    "text": prompt,
                    "result": result,
                    "server_time": now_iso(),
                })
            elif kind == "ping":
                await websocket.send_json({"type": "pong", "server_time": now_iso()})
            else:
                await websocket.send_json({"type": "error", "text": "Unsupported event"})
    except WebSocketDisconnect:
        pass
    finally:
        async with state_lock:
            rooms.get(room_id, {}).pop(client_id, None)
            room_names.get(room_id, {}).pop(client_id, None)
            if not rooms.get(room_id):
                rooms.pop(room_id, None)
                room_names.pop(room_id, None)
        await broadcast(room_id, {"type": "presence", "members": await room_snapshot(room_id)})
        await broadcast(room_id, {"type": "system", "text": f"{display_name} left the room", "server_time": now_iso()})
