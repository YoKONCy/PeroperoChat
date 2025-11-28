import os
import json
import re
from typing import List, Dict, Any, Optional
import httpx
from .config_loader import get_config
from .db import add_memory_item, list_memory_items, soft_delete_memory_item, find_memory_item_id_by_type_text

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

def _boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v or "").strip().lower()
    return s in ("true", "1", "yes", "y", "on")

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

def parse_triggers_from_text(s: str) -> Dict[str, bool]:
    t = str(s or "")
    try:
        m = re.search(r"\[\[MEMTRG\]\]([\s\S]*?)\[\[/MEMTRG\]\]", t)
        if not m:
            return {"event": False, "user_hobby": False, "assistant_hobby": False}
        js = m.group(1) or "{}"
        obj = json.loads(js)
        return {
            "event": _boolish(obj.get("事件记录触发器", False)),
            "user_hobby": _boolish(obj.get("用户爱好记录触发器", False)),
            "assistant_hobby": _boolish(obj.get("助手爱好记录触发器", False)),
        }
    except Exception:
        return {"event": False, "user_hobby": False, "assistant_hobby": False}

def _strip_hidden_segments(s: str) -> str:
    t = str(s or "")
    try:
        t = re.sub(r"\[\[PEROCUE\]\][\s\S]*?\[\[/PEROCUE\]\]", "", t)
        t = re.sub(r"\[\[MEMTRG\]\][\s\S]*?\[\[/MEMTRG\]\]", "", t)
        return t
    except Exception:
        return t

def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    t = str(text or "").strip()
    if not t:
        return None
    try:
        return json.loads(t)
    except Exception:
        pass
    # remove markdown code fences ```json ... ``` or ``` ... ```
    if t.startswith("```"):
        try:
            t2 = t
            t2 = re.sub(r"^```\w*\s*", "", t2)
            t2 = re.sub(r"\s*```$", "", t2)
            return json.loads(t2.strip())
        except Exception:
            pass
    # extract first {...} block
    try:
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(t[start:end+1])
    except Exception:
        pass
    return None

async def extract_and_store(messages: List[Dict[str, Any]], full_text: str, model: str, authorization: Optional[str], api_base: Optional[str]) -> Dict[str, Any]:
    cfg = get_config()
    base = (api_base or cfg["openai"]["api_base"] or "https://api.openai.com").rstrip('/')
    auth = authorization
    triggers = parse_triggers_from_text(full_text)
    try:
        print("[memory] triggers", triggers)
    except Exception:
        pass
    results = {"created": []}
    if not auth:
        return results
    limited: List[Dict[str, str]] = []
    lim_n = int(os.getenv("SUMMARY_MAX_CONTEXT", "6") or "6")
    cc = 0
    for mm in reversed(messages + [{"role": "assistant", "content": full_text}]):
        if not _is_normal_msg(mm):
            continue
        limited.append({"role": str(mm.get("role")), "content": _strip_hidden_segments(mm.get("content"))})
        cc += 1
        if cc >= lim_n:
            break
    limited.reverse()
    combined = bool(triggers.get("event")) and bool(triggers.get("user_hobby") or triggers.get("assistant_hobby"))
    if combined:
        csp = cfg.get("secondary_prompts", {}).get("combined_summary_prompt", "仅输出JSON：{\"summary\": \"...\", \"hobby\": \"...\"}")
        payload = {"model": model, "messages": [{"role": "system", "content": csp}] + limited, "temperature": 0.2, "stream": False}
        summary = ""
        hobby_text = ""
        meta_obj: Dict[str, Any] = {}
        _log_prompt(payload.get("messages", []))
        to_sec = int(cfg.get("timeouts", {}).get("combined_timeout", 60) or 60)
        async with httpx.AsyncClient(timeout=httpx.Timeout(read=to_sec, connect=30, write=30, pool=30)) as c:
            r = await c.post(base + "/v1/chat/completions", headers={"Authorization": auth, "Content-Type": "application/json"}, json=payload)
            if r.status_code == 200:
                txt = str(r.json().get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
                _log_reply(txt)
                obj = _try_parse_json(txt)
                if isinstance(obj, dict):
                    meta_obj = obj
                    sv = str(obj.get("summary", "")).strip()
                    summary = sv[:50]
                    hobby_text = str(obj.get("hobby", "")).strip()
                else:
                    summary = (txt.splitlines()[0] if txt else "")[:50]
                    hobby_text = txt.strip()
            else:
                try:
                    print("[memory] combined status", r.status_code)
                except Exception:
                    pass
        evt_text = (summary or full_text[:50]).strip()
        if not find_memory_item_id_by_type_text("event", evt_text):
            mid_evt = add_memory_item("event", evt_text, meta_obj or {})
            results["created"].append(mid_evt)
        if triggers.get("user_hobby"):
            uh_text = (hobby_text or "").strip()
            if not find_memory_item_id_by_type_text("user_hobby", uh_text):
                mid_uh = add_memory_item("user_hobby", uh_text, meta_obj or {})
                results["created"].append(mid_uh)
        if triggers.get("assistant_hobby"):
            ah_text = (hobby_text or "").strip()
            if not find_memory_item_id_by_type_text("assistant_hobby", ah_text):
                mid_ah = add_memory_item("assistant_hobby", ah_text, meta_obj or {})
                results["created"].append(mid_ah)
        return results
    if triggers.get("event"):
        esp = cfg.get("secondary_prompts", {}).get("event_summary_prompt", "仅输出JSON：{\"summary\": \"...\"}")
        payload = {"model": model, "messages": [{"role": "system", "content": esp}] + limited, "temperature": 0.2, "stream": False}
        summary = ""
        meta_obj: Dict[str, Any] = {}
        _log_prompt(payload.get("messages", []))
        to_sec_evt = int(cfg.get("timeouts", {}).get("event_timeout", 60) or 60)
        async with httpx.AsyncClient(timeout=httpx.Timeout(read=to_sec_evt, connect=30, write=30, pool=30)) as c:
            r = await c.post(base + "/v1/chat/completions", headers={"Authorization": auth, "Content-Type": "application/json"}, json=payload)
            if r.status_code == 200:
                txt = str(r.json().get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
                _log_reply(txt)
                obj = _try_parse_json(txt)
                if isinstance(obj, dict):
                    meta_obj = obj
                    sv = str(obj.get("summary", "")).strip()
                    summary = sv[:50]
                else:
                    summary = (txt.splitlines()[0] if txt else "")[:50]
            else:
                try:
                    print("[memory] event summary status", r.status_code)
                except Exception:
                    pass
        evt_text = (summary or full_text[:50]).strip()
        if not find_memory_item_id_by_type_text("event", evt_text):
            mid = add_memory_item("event", evt_text, meta_obj or {})
            try:
                print("[memory] created event", mid)
            except Exception:
                pass
            results["created"].append(mid)
    if triggers.get("user_hobby") or triggers.get("assistant_hobby"):
        hsp = cfg.get("secondary_prompts", {}).get("hobby_summary_prompt", "仅输出JSON：{\"hobby\": \"...\"}")
        payload = {"model": model, "messages": [{"role": "system", "content": hsp}] + limited, "temperature": 0.2, "stream": False}
        hobby_text = ""
        meta_obj: Dict[str, Any] = {}
        _log_prompt(payload.get("messages", []))
        to_sec_hb = int(cfg.get("timeouts", {}).get("hobby_timeout", 45) or 45)
        async with httpx.AsyncClient(timeout=httpx.Timeout(read=to_sec_hb, connect=30, write=30, pool=30)) as c3:
            r3 = await c3.post(base + "/v1/chat/completions", headers={"Authorization": auth, "Content-Type": "application/json"}, json=payload)
            if r3.status_code == 200:
                txt = str(r3.json().get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
                _log_reply(txt)
                obj = _try_parse_json(txt)
                if isinstance(obj, dict):
                    meta_obj = obj
                    hobby_text = str(obj.get("hobby", "")).strip()
                else:
                    hobby_text = txt.strip()
            else:
                try:
                    print("[memory] hobby status", r3.status_code)
                except Exception:
                    pass
        if triggers.get("user_hobby"):
            uh_text = (hobby_text or "").strip()
            if not find_memory_item_id_by_type_text("user_hobby", uh_text):
                mid = add_memory_item("user_hobby", uh_text, meta_obj or {})
                results["created"].append(mid)
                try:
                    print("[memory] created user_hobby", mid)
                except Exception:
                    pass
        if triggers.get("assistant_hobby"):
            ah_text = (hobby_text or "").strip()
            if not find_memory_item_id_by_type_text("assistant_hobby", ah_text):
                mid = add_memory_item("assistant_hobby", ah_text, meta_obj or {})
                results["created"].append(mid)
                try:
                    print("[memory] created assistant_hobby", mid)
                except Exception:
                    pass
    return results

async def preprocess_and_select(messages: List[Dict[str, Any]], model: str, authorization: Optional[str], api_base: Optional[str], max_items: int = 500) -> List[Dict[str, Any]]:
    cfg = get_config()
    base = (api_base or cfg["openai"]["api_base"] or "https://api.openai.com").rstrip('/')
    auth = authorization
    if not auth:
        try:
            print("[preprocess] skip: no assistant auth")
        except Exception:
            pass
        return []
    all_items = list_memory_items(None, limit=max_items, offset=0)
    try:
        print("[preprocess] memory_items", len(all_items))
    except Exception:
        pass
    limited_raw: List[Dict[str, Any]] = []
    cc = 0
    for mm in reversed(messages):
        if _is_normal_msg(mm):
            limited_raw.append({"role": mm.get("role"), "content": _strip_hidden_segments(mm.get("content"))})
            cc += 1
            if cc >= 10:
                break
    limited_raw.reverse()
    prompt = cfg.get("secondary_prompts", {}).get("memory_preprocess_prompt", "仅输出JSON：{\"selected\": [{\"id\": 1, \"type\": \"event\", \"created_at\": \"...\"}], \"reason\": \"...\"}")
    content = {
        "messages": limited_raw,
        "memory_items": [{"id": i["id"], "type": i["type"], "text": i["text"], "created_at": i.get("created_at", "")} for i in all_items],
    }
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(content, ensure_ascii=False)}], "temperature": 0.2, "stream": False}
    _log_prompt(payload.get("messages", []))
    ids: List[int] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(read=int(get_config().get("timeouts", {}).get("select_timeout", 60) or 60), connect=30, write=30, pool=30)) as c:
        try:
            r = await c.post(base + "/v1/chat/completions", headers={"Authorization": auth, "Content-Type": "application/json"}, json=payload)
            if r.status_code == 200:
                txt = str(r.json().get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
                _log_reply(txt)
                obj = _try_parse_json(txt)
                if isinstance(obj, dict):
                    arr = obj.get("selected", [])
                    if isinstance(arr, list):
                        for it in arr:
                            try:
                                ids.append(int(str((it or {}).get("id", "")).strip()))
                            except Exception:
                                continue
            else:
                try:
                    body = r.text
                    body = (body[:400] + "...") if len(body) > 400 else body
                    print("[preprocess] non-200", r.status_code, body)
                except Exception:
                    pass
        except Exception as e:
            try:
                print("[preprocess] http error", str(e))
            except Exception:
                pass
    selected = [i for i in all_items if int(i["id"]) in set(ids)]
    try:
        print("[memory] selected_ids", ids)
    except Exception:
        pass
    return selected[:6]

def build_memory_system(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not items:
        return []
    lines: List[str] = []
    for it in items:
        t = it.get("type")
        txt = it.get("text") or ""
        if t == "event":
            lines.append(f"<event>{txt}</event>")
        elif t == "user_hobby":
            lines.append(f"<user_hobby>{txt}</user_hobby>")
        elif t == "assistant_hobby":
            lines.append(f"<assistant_hobby>{txt}</assistant_hobby>")
    if not lines:
        return []
    joined = "\n".join(lines)
    return [{"role": "system", "content": joined}]

async def maintain_events(model: str, authorization: Optional[str], api_base: Optional[str]) -> Dict[str, Any]:
    cfg = get_config()
    base = (api_base or cfg["openai"]["api_base"] or "https://api.openai.com").rstrip('/')
    auth = authorization
    if not auth:
        return {"ok": False, "error": "no auth"}
    items = list_memory_items("event", limit=200, offset=0)
    items = [i for i in items if not str(i.get("text","")) == ""]
    merged = 0
    for i in range(len(items) - 1):
        a = items[i]
        b = items[i + 1]
        prompt = cfg.get("maintenance", {}).get("merge_prompt", "请将以下两条相邻事件摘要再次浓缩为约50字的综合摘要，只输出一行文本。")
        content = f"摘要A：{a['text']}\n摘要B：{b['text']}"
        payload = {"model": model, "messages": [{"role": "system", "content": prompt}, {"role": "assistant", "content": content}], "temperature": 0.2, "stream": False}
        _log_prompt(payload.get("messages", []))
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.post(base + "/v1/chat/completions", headers={"Authorization": auth, "Content-Type": "application/json"}, json=payload)
            if r.status_code == 200:
                out = str(r.json().get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
                _log_reply(out)
                mid = add_memory_item("event", out or content[:120], {"merged_from": [a["id"], b["id"]]})
                soft_delete_memory_item(a["id"]) 
                soft_delete_memory_item(b["id"]) 
                merged += 1
    return {"ok": True, "merged": merged}
