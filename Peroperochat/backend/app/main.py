import os
import json
from typing import List, Optional
from datetime import datetime
import time

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from .config_loader import get_config
from .db import init_db, list_memory_items, add_memory_item, soft_delete_memory_item, increment_conversation_count, reset_all as db_reset_all
from .memory_service import preprocess_and_select, build_memory_system, extract_and_store, maintain_events, parse_triggers_from_text
import asyncio
import urllib.parse
from uuid import uuid4
import re
def _debug_enabled() -> bool:
    v = str(os.getenv("DEBUG_LOG_PROMPTS", "1")).strip().lower()
    return v not in ("0", "false", "no", "off")

def _log_prompt(msgs: list):
    if not _debug_enabled():
        return
    try:
        print("[prompt] messages", json.dumps(msgs, ensure_ascii=False))
    except Exception:
        pass

def _log_reply(text: str):
    if not _debug_enabled():
        return
    try:
        print("[reply] content", str(text or ""))
    except Exception:
        pass

async def _get_matching_summaries(msgs: List[dict], max_scan: int = 1000, max_prompts: int = 6) -> List[str]:
    try:
        return []
    except Exception:
        return []


def _is_placeholder_text(s: str) -> bool:
    t = str(s or "").strip()
    if not t:
        return True
    low = t.lower()
    if "__loading__" in low:
        return True
    if ("伙伴正在思考中..." in t) or ("正在思考" in t) or ("思考中" in t) or ("组织回复" in t):
        return True
    if low.startswith("thinking") or low.startswith("generating") or low.startswith("loading"):
        return True
    return False

def _is_normal_msg(mm: dict) -> bool:
    r = str(mm.get("role", "")).strip().lower()
    if r not in ("user", "assistant"):
        return False
    c = str(mm.get("content", ""))
    if _is_placeholder_text(c):
        return False
    return True

def _strip_hidden_segments(s: str) -> str:
    t = str(s or "")
    try:
        t = re.sub(r"\[\[PEROCUE\]\][\s\S]*?\[\[/PEROCUE\]\]", "", t)
        t = re.sub(r"\[\[MEMTRG\]\][\s\S]*?\[\[/MEMTRG\]\]", "", t)
        return t
    except Exception:
        return t

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None


class ChatReply(BaseModel):
    content: str
    memory_created: Optional[bool] = False
    memory_ids: Optional[List[int]] = []


app = FastAPI(title="Peroperochat 后端")
_cfg = get_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ts = time.time()
        response = await call_next(request)
        dt = (time.time() - ts) * 1000.0
        try:
            print("[http]", request.method, request.url.path, "->", response.status_code, f"{dt:.1f}ms")
        except Exception:
            pass
        return response

app.add_middleware(LoggingMiddleware)

static_dir = os.path.join(os.path.dirname(__file__), "static")
models_dir = os.path.join(static_dir, "models")
os.makedirs(models_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
    except Exception:
        pass


@app.post("/api/chat", response_model=ChatReply)
async def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
    api_base: str | None = None,
    assistant_authorization: str | None = Header(default=None, alias="X-Assistant-Authorization"),
    assistant_api_base: str | None = None,
    assistant_model: str | None = Header(default=None, alias="X-Assistant-Model"),
    disable_memory: str | None = Header(default=None, alias="X-Disable-Memory"),
):
    cfg = get_config()
    env_api_base = cfg["openai"]["api_base"] or os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    model = (request.model or "").strip()
    if not model or model == "请先获取模型":
        raise HTTPException(status_code=400, detail="缺少模型ID：请先获取并选择模型")
    auth_header = authorization
    base = (api_base or env_api_base).rstrip("/")
    content = ""
    if not auth_header:
        base_msgs = [m.model_dump() for m in request.messages]
        _log_prompt(base_msgs)
        content = "后端未配置模型API密钥，返回占位回复：" + (request.messages[-1].content if request.messages else "")
    else:
        url = base + "/v1/chat/completions"
        base_msgs = [m.model_dump() for m in request.messages]
        final_msgs = base_msgs
        payload = {
            "model": model,
            "messages": final_msgs,
            "temperature": request.temperature,
            "stream": False,
        }
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            payload["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            payload["presence_penalty"] = request.presence_penalty
        headers = {"Authorization": auth_header, "Content-Type": "application/json"}
    if assistant_authorization and assistant_model:
        try:
            abase = (assistant_api_base or base).rstrip("/")
            assistant_model_decoded = urllib.parse.unquote(assistant_model)
            assistant_authorization_decoded = urllib.parse.unquote(assistant_authorization)
            nm_count = sum(1 for m in base_msgs if _is_normal_msg(m))
            if nm_count > 1:
                selected = await preprocess_and_select(base_msgs, assistant_model_decoded, assistant_authorization_decoded, abase)
                sys_mem = build_memory_system(selected)
                final_msgs = sys_mem + base_msgs if sys_mem else base_msgs
                payload["messages"] = final_msgs
            else:
                try:
                    print("[preprocess] skip: first-turn or insufficient history", nm_count)
                except Exception:
                    pass
                payload["messages"] = final_msgs
        except Exception:
            payload["messages"] = final_msgs
        _log_prompt(payload.get("messages", []))
        to_sec = int(_cfg.get("timeouts", {}).get("chat_timeout", 120) or 120)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(read=to_sec, connect=30, write=30, pool=30)) as client:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code != 200:
                    raise HTTPException(status_code=502, detail=r.text)
                data = r.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail="模型接口超时")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=str(e))
        sid = uuid4().hex[:32]
        msgs = [m.model_dump() for m in request.messages] + [{"role": "assistant", "content": content}]
    _log_reply(content)
    async def persist():
        try:
            pass
        except Exception as e:
            print("[persist-chat] error", e)
    await persist()
    try:
        increment_conversation_count()
    except Exception:
        pass
    created_ids: List[int] = []
    try:
        abase = (assistant_api_base or base).rstrip("/")
        auth2 = (urllib.parse.unquote(assistant_authorization) if assistant_authorization else auth_header)
        model2 = (urllib.parse.unquote(assistant_model) if assistant_model else model)
        no_mem = str(disable_memory or "").strip().lower() in ("1","true","yes","on")
        if auth2 and not no_mem:
            r2 = await extract_and_store([m.model_dump() for m in request.messages], content, model2, auth2, abase)
            created_ids = list(r2.get("created", [])) if isinstance(r2, dict) else []
    except Exception:
        created_ids = []
    return ChatReply(content=content, memory_created=bool(created_ids), memory_ids=[int(i) for i in created_ids])


@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
    api_base: str | None = None,
    assistant_authorization: str | None = Header(default=None, alias="X-Assistant-Authorization"),
    assistant_api_base: str | None = None,
    assistant_model: str | None = Header(default=None, alias="X-Assistant-Model"),
    disable_memory: str | None = Header(default=None, alias="X-Disable-Memory"),
):
    cfg = get_config()
    env_api_key = cfg["openai"]["api_key"] or os.getenv("OPENAI_API_KEY", "")
    env_api_base = cfg["openai"]["api_base"] or os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    model = (request.model or "").strip()
    if not model or model == "请先获取模型":
        raise HTTPException(status_code=400, detail="缺少模型ID：请先获取并选择模型")
    auth_header = authorization or (f"Bearer {env_api_key}" if env_api_key else None)
    base = (api_base or env_api_base).rstrip("/")
    if not auth_header:
        raise HTTPException(status_code=400, detail="缺少API秘钥：请在后端环境或请求头中提供")
    url = base + "/v1/chat/completions"
    base_msgs = [m.model_dump() for m in request.messages]
    final_msgs = base_msgs
    if assistant_authorization and assistant_model:
        try:
            abase = (assistant_api_base or base).rstrip("/")
            nm_count = sum(1 for m in base_msgs if _is_normal_msg(m))
            if nm_count > 1:
                selected = await preprocess_and_select(base_msgs, urllib.parse.unquote(assistant_model), urllib.parse.unquote(assistant_authorization), abase)
                sys_mem = build_memory_system(selected)
                if sys_mem:
                    final_msgs = sys_mem + final_msgs
            else:
                try:
                    print("[preprocess] skip: first-turn or insufficient history", nm_count)
                except Exception:
                    pass
        except Exception:
            pass
    _log_prompt(final_msgs)
    payload = {
        "model": model,
        "messages": final_msgs,
        "temperature": request.temperature,
        "stream": True,
    }
    if request.top_p is not None:
        payload["top_p"] = request.top_p
    if request.frequency_penalty is not None:
        payload["frequency_penalty"] = request.frequency_penalty
    if request.presence_penalty is not None:
        payload["presence_penalty"] = request.presence_penalty
    headers = {"Authorization": auth_header, "Content-Type": "application/json"}

    async def event_generator():
        sid = uuid4().hex[:32]
        acc: List[str] = []
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    text = await resp.aread()
                    raise HTTPException(status_code=502, detail=text.decode("utf-8", errors="ignore"))
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[len("data: "):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            obj = json.loads(data_str)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content_piece = delta.get("content")
                            if content_piece:
                                acc.append(content_piece)
                                yield content_piece
                        except Exception:
                            continue
        msgs = [m.model_dump() for m in request.messages] + [{"role": "assistant", "content": "".join(acc)}]
        _log_reply("".join(acc))
        async def persist():
            try:
                pass
            except Exception as e:
                print("[persist-stream] error", e)
        await persist()
        try:
            abase = (assistant_api_base or base).rstrip("/")
            auth2 = (urllib.parse.unquote(assistant_authorization) if assistant_authorization else auth_header)
            model2 = (urllib.parse.unquote(assistant_model) if assistant_model else model)
            no_mem = str(disable_memory or "").strip().lower() in ("1","true","yes","on")
            if auth2 and not no_mem:
                await extract_and_store([m.model_dump() for m in request.messages], "".join(acc), model2, auth2, abase)
        except Exception:
            pass

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")


@app.post("/api/models/3d/upload")
async def upload_model(file: UploadFile = File(...)):
    filename = file.filename or "model.glb"
    save_path = os.path.join(models_dir, filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    url_path = "/static/models/" + filename
    return JSONResponse({"url": url_path})


@app.get("/api/models/3d/sample")
async def sample_model():
    sample = os.path.join(models_dir, "sample.glb")
    if os.path.exists(sample):
        return JSONResponse({"url": "/static/models/sample.glb"})
    return JSONResponse({"url": ""})


@app.get("/api/models")
async def list_models(authorization: str | None = Header(default=None), api_base: str | None = None):
    default_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    auth_header = authorization
    if not auth_header:
        raise HTTPException(status_code=400, detail="缺少API秘钥：请在后端环境或请求头中提供")
    base = (api_base or default_base).rstrip("/")
    url = base + "/v1/models"
    headers = {"Authorization": auth_header}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=r.text)
        return JSONResponse(r.json())

@app.get("/api/config/prompts")
async def get_default_prompts():
    cfg = get_config()
    p = cfg.get("prompts", {})
    return JSONResponse({
        "system_prompt_default": p.get("system_prompt_default", ""),
        "persona_prompt_default": p.get("persona_prompt_default", ""),
        "post_prompt_default": p.get("post_prompt_default", ""),
    })

@app.get("/api/config/semantic")
async def get_semantic_config():
    cfg = get_config()
    n = int(os.getenv("SEMANTIC_WRITE_EVERY_N", str(cfg["semantic"]["write_every_n"])) or str(cfg["semantic"]["write_every_n"]))
    return JSONResponse({
        "write_every_n": n,
    })

@app.post("/api/reset")
async def reset_all_data():
    try:
        db_reset_all()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

# 旧语义检索接口已移除

@app.get("/api/memory/time/summary")
async def time_summary(start: str, end: str):
    return JSONResponse({"results": []})



@app.get("/api/db/ping")
async def db_ping():
    return JSONResponse({"configured": False, "ok": False, "error": "数据库功能已禁用"})


@app.get("/api/db/version")
async def db_version():
    return JSONResponse({"configured": False, "version": "", "error": "数据库功能已禁用"})

@app.get("/api/db/tables")
async def db_tables():
    return JSONResponse({"tables": []})

    

@app.get("/api/db/records/summary")
async def db_records_summary(limit: int = 100):
    lim = 100 if limit is None else max(1, min(int(limit), 5000))
    return JSONResponse({"results": []})

# 旧向量记录接口已移除

class DbConfig(BaseModel):
    path: Optional[str] = None

@app.post("/api/db/configure")
async def db_configure(cfg: DbConfig | None = Body(default=None)):
    return JSONResponse({"configured": False, "ok": False, "error": "数据库功能已禁用"})
@app.post("/api/debug/insert_summary")
async def debug_insert_summary():
    return JSONResponse({"ok": True})

# 记忆API
class MemoryInsert(BaseModel):
    type: str
    text: str

@app.get("/api/memory/list")
async def memory_list(type: Optional[str] = Query(default=None), limit: int = Query(default=50), offset: int = Query(default=0)):
    try:
        items = list_memory_items(type, limit=limit, offset=offset)
        return JSONResponse({"results": items})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/insert")
async def memory_insert(body: MemoryInsert):
    try:
        mid = add_memory_item(body.type, body.text, {})
        return JSONResponse({"ok": True, "id": mid})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/delete")
async def memory_delete(id: int = Query(...)):
    try:
        ok = soft_delete_memory_item(id)
        return JSONResponse({"ok": ok})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MemorySelectReq(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None

@app.post("/api/memory/select")
async def memory_select(
    req: MemorySelectReq,
    authorization: str | None = Header(default=None, alias="X-Assistant-Authorization"),
    api_base: str | None = None,
    assistant_api_base: str | None = None,
):
    try:
        model = (req.model or "").strip()
        if not model:
            raise HTTPException(status_code=400, detail="缺少模型ID")
        abase = (assistant_api_base or api_base)
        selected = await preprocess_and_select([m.model_dump() for m in req.messages], model, authorization, abase)
        return JSONResponse({"results": selected})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MemoryMaintainReq(BaseModel):
    model: str

@app.post("/api/memory/maintain")
async def memory_maintain(
    req: MemoryMaintainReq,
    authorization: str | None = Header(default=None, alias="X-Assistant-Authorization"),
    api_base: str | None = None,
    assistant_api_base: str | None = None,
):
    try:
        abase = (assistant_api_base or api_base)
        r = await maintain_events(req.model, authorization, abase)
        return JSONResponse(r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
