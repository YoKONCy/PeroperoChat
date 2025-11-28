import os
import configparser

def _bool(s: str) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")

def get_config():
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "config.ini")
    cp = configparser.ConfigParser()
    cp.read(path, encoding="utf-8")
    openai = {
        "api_key": cp.get("openai", "api_key", fallback="").strip(),
        "api_base": cp.get("openai", "api_base", fallback="https://api.openai.com").strip(),
    }
    summary = {
        "prompt": cp.get("summary", "prompt", fallback="请总结以下对话，最多300字").strip(),
    }
    secondary_prompts = {
        "event_summary_prompt": cp.get(
            "secondary_prompts",
            "event_summary_prompt",
            fallback="你是一名事件记录员，请用客观白描描述对话中的事件，最多50字。仅输出JSON：{\"summary\": \"...\"}。只输出JSON，不要任何解释或附加文本。"
        ).strip(),
        "hobby_summary_prompt": cp.get(
            "secondary_prompts",
            "hobby_summary_prompt",
            fallback="你是一名爱好记录员，请识别新增爱好并用一句话概括；若无新增则输出空字符串。仅输出JSON：{\"hobby\": \"...\"}。只输出JSON，不要任何解释或附加文本。"
        ).strip(),
        "combined_summary_prompt": cp.get(
            "secondary_prompts",
            "combined_summary_prompt",
            fallback="你同时担任事件记录员与爱好记录员。根据最近对话生成一个JSON对象，格式为 {\"summary\": \"事件摘要，最多50字\", \"hobby\": \"本次新增的爱好，若无则空字符串\"}。仅输出JSON，不要任何解释或附加文本。"
        ).strip(),
        "memory_preprocess_prompt": cp.get(
            "secondary_prompts",
            "memory_preprocess_prompt",
            fallback="仅输出JSON：{\"selected\": [{\"id\": 1, \"type\": \"event\", \"created_at\": \"...\"}], \"reason\": \"...\"}"
        ).strip(),
    }
    maintenance = {
        "merge_prompt": cp.get("maintenance", "merge_prompt", fallback="请将以下两条相邻事件摘要再次浓缩为约50字的综合摘要，只输出一行文本。").strip(),
    }
    timeouts = {
        "chat_timeout": int(cp.get("timeouts", "chat_timeout", fallback="120") or "120"),
        "combined_timeout": int(cp.get("timeouts", "combined_timeout", fallback="60") or "60"),
        "event_timeout": int(cp.get("timeouts", "event_timeout", fallback="60") or "60"),
        "hobby_timeout": int(cp.get("timeouts", "hobby_timeout", fallback="45") or "45"),
        "select_timeout": int(cp.get("timeouts", "select_timeout", fallback="60") or "60"),
        "maintain_timeout": int(cp.get("timeouts", "maintain_timeout", fallback="60") or "60"),
    }
    semantic = {
        "search_k": int(cp.get("semantic", "search_k", fallback="10") or "10"),
        "write_every_n": int(cp.get("semantic", "write_every_n", fallback="10") or "10"),
    }
    prompts = {
        "system_prompt_default": cp.get("prompts", "system_prompt_default", fallback="").strip(),
        "persona_prompt_default": cp.get("prompts", "persona_prompt_default", fallback="").strip(),
        "post_prompt_default": cp.get("prompts", "post_prompt_default", fallback=os.getenv("POST_SYSTEM_PROMPT", "")).strip(),
    }
    return {
        "openai": openai,
        "summary": summary,
        "secondary_prompts": secondary_prompts,
        "maintenance": maintenance,
        "timeouts": timeouts,
        "semantic": semantic,
        "prompts": prompts,
        "_path": path,
    }

def save_config(updates: dict):
    cfg = get_config()
    cp = configparser.ConfigParser()
    cp.read(cfg["_path"], encoding="utf-8")
    for section, kv in updates.items():
        if not cp.has_section(section):
            cp.add_section(section)
        for k, v in kv.items():
            cp.set(section, k, str(v))
    with open(cfg["_path"], "w", encoding="utf-8") as f:
        cp.write(f)
