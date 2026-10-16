"""AI connection layer: Claude (primary) and Chat Astra (secondary).

API keys live only on the server — in environment variables or in
instance/secrets.json (mode 600) written from the Settings page. They are never
rendered into templates or returned by any endpoint; the browser only ever sees
"connected / not connected".

Chat Astra is reached through an OpenAI-compatible /chat/completions endpoint
whose base URL and model are configurable, so it can point at whichever Astra
deployment Vestige uses.
"""
import json
import os
import re

import requests
from flask import current_app

from . import db

CLAUDE_MODELS = {
    "claude-opus-5-5": "Claude Opus 5.5 — deepest strategy",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 — faster, lower cost",
    "claude-haiku-5-5": "Claude Haiku 5.5 — quick drafts",
}
DEFAULT_CLAUDE_MODEL = "claude-opus-5-5"
SECRET_KEYS = ("anthropic_api_key", "astra_api_key")


class AIError(Exception):
    pass


# ---------------------------------------------------------------- secrets ----

def _secrets_path():
    return os.path.join(current_app.instance_path, "secrets.json")


def _load_secrets():
    try:
        with open(_secrets_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_secret(name, value):
    if name not in SECRET_KEYS:
        raise ValueError(name)
    data = _load_secrets()
    if value:
        data[name] = value.strip()
    else:
        data.pop(name, None)
    os.makedirs(current_app.instance_path, exist_ok=True)
    path = _secrets_path()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def _secret(name):
    env = {"anthropic_api_key": "ANTHROPIC_API_KEY", "astra_api_key": "ASTRA_API_KEY"}[name]
    return os.environ.get(env) or _load_secrets().get(name)


def config():
    """Non-secret configuration, safe to render."""
    return {
        "primary": db.get_setting("ai_primary", "claude"),
        "fallback": db.get_setting("ai_fallback", "on") == "on",
        "claude_model": db.get_setting("claude_model", DEFAULT_CLAUDE_MODEL),
        "claude_effort": db.get_setting("claude_effort", "high"),
        "astra_base_url": db.get_setting("astra_base_url", os.environ.get("ASTRA_BASE_URL", "")),
        "astra_model": db.get_setting("astra_model", os.environ.get("ASTRA_MODEL", "")),
    }


def status():
    cfg = config()
    claude_ok = bool(_secret("anthropic_api_key"))
    astra_ok = bool(_secret("astra_api_key") and cfg["astra_base_url"] and cfg["astra_model"])
    active = cfg["primary"] if {"claude": claude_ok, "astra": astra_ok}[cfg["primary"]] else (
        "claude" if claude_ok else ("astra" if astra_ok else None))
    return {
        "claude": claude_ok,
        "astra": astra_ok,
        "active": active,
        "label": model_label(active, cfg) if active else "Not connected",
        **cfg,
    }


def model_label(provider, cfg=None):
    cfg = cfg or config()
    if provider == "claude":
        return cfg["claude_model"]
    if provider == "astra":
        return f"Chat Astra · {cfg['astra_model'] or 'unconfigured'}"
    return "manual"


# -------------------------------------------------------------- providers ----

def _call_claude(system, prompt, max_tokens, cfg):
    import anthropic

    key = _secret("anthropic_api_key")
    if not key:
        raise AIError("Claude is not connected. Add the API key in Settings.")
    client = anthropic.Anthropic(api_key=key, timeout=600.0)
    try:
        # Server-side refusal fallback ("default" routing) keeps long strategy
        # runs from dying on a false-positive safety decline.
        resp = client.beta.messages.create(
            model=cfg["claude_model"],
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": cfg["claude_effort"]},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        raise AIError("Claude rejected the API key. Check it in Settings.")
    except anthropic.RateLimitError:
        raise AIError("Claude rate limit reached — try again in a minute.")
    except anthropic.APIStatusError as e:
        raise AIError(f"Claude API error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise AIError("Could not reach the Claude API (network).")
    if resp.stop_reason == "refusal":
        raise AIError("Claude declined this request. Rephrase the brief and retry.")
    text = "".join(b.text for b in resp.content if b.type == "text")
    if resp.stop_reason == "max_tokens":
        raise AIError("The response was cut off (too long). Narrow the request and retry.")
    return text, resp.model


def _call_astra(system, prompt, max_tokens, cfg):
    key = _secret("astra_api_key")
    if not (key and cfg["astra_base_url"] and cfg["astra_model"]):
        raise AIError("Chat Astra is not configured. Add base URL, model and key in Settings.")
    url = cfg["astra_base_url"].rstrip("/") + "/chat/completions"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": cfg["astra_model"],
                "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            },
            timeout=300,
        )
    except requests.RequestException as e:
        raise AIError(f"Could not reach Chat Astra: {e.__class__.__name__}")
    if r.status_code >= 400:
        raise AIError(f"Chat Astra error ({r.status_code}).")
    try:
        return r.json()["choices"][0]["message"]["content"], f"astra:{cfg['astra_model']}"
    except (ValueError, KeyError, IndexError):
        raise AIError("Chat Astra returned an unexpected response shape.")


def complete(system, prompt, provider=None, max_tokens=16000):
    """Run a completion. Returns (text, model_used)."""
    cfg = config()
    order = [provider or cfg["primary"]]
    if cfg["fallback"]:
        order.append("astra" if order[0] == "claude" else "claude")
    calls = {"claude": _call_claude, "astra": _call_astra}
    errors = []
    for p in order:
        try:
            return calls[p](system, prompt, max_tokens, cfg)
        except AIError as e:
            errors.append(str(e))
    raise AIError(" / ".join(errors))


def parse_json(text):
    """Extract the first JSON object/array from a model response."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except ValueError:
                continue
    raise AIError("The model did not return valid JSON. Retry the generation.")


def complete_json(system, prompt, provider=None, max_tokens=16000):
    text, model = complete(system, prompt, provider, max_tokens)
    return parse_json(text), model


# ------------------------------------------------------ web research (Claude) ----

WEB_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 15},
    {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 8},
]


def _sources(content):
    seen, out = set(), []
    for block in content:
        btype = getattr(block, "type", "")
        items = []
        if btype == "web_search_tool_result" and isinstance(getattr(block, "content", None), list):
            items = [(getattr(r, "url", ""), getattr(r, "title", "")) for r in block.content]
        elif btype == "text":
            items = [(getattr(c, "url", ""), getattr(c, "title", "")) for c in (getattr(block, "citations", None) or [])]
        for url, title in items:
            if url and url not in seen:
                seen.add(url)
                out.append({"url": url, "title": title or url})
    return out


def research_json(system, prompt, provider=None, max_tokens=32000):
    """Claude with web search/fetch; returns (data, model, sources, used_web).

    Falls back to a no-web completion (e.g. Chat Astra) when Claude is unavailable,
    flagged via used_web=False so the UI can say the dossier is not web-verified.
    """
    import anthropic

    cfg = config()
    key = _secret("anthropic_api_key")
    if provider == "astra" or not key:
        data, model = complete_json(system, prompt + "\n\n(No web access in this run: rely only on the material "
                                    "provided and mark every unverified statement as such.)", provider)
        return data, model, [], False
    client = anthropic.Anthropic(api_key=key, timeout=900.0)
    messages = [{"role": "user", "content": prompt}]
    content = []
    try:
        for _ in range(6):  # server tools may pause a long turn; continue it
            with client.beta.messages.stream(
                model=cfg["claude_model"], max_tokens=max_tokens, system=system, messages=messages,
                tools=WEB_TOOLS, output_config={"effort": cfg["claude_effort"]},
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            ) as stream:
                resp = stream.get_final_message()
            content.extend(resp.content)
            if resp.stop_reason != "pause_turn":
                break
            messages = messages + [{"role": "assistant", "content": resp.content}]
    except anthropic.AuthenticationError:
        raise AIError("Claude rejected the API key. Check it in Settings.")
    except anthropic.RateLimitError:
        raise AIError("Claude rate limit reached — try again in a minute.")
    except anthropic.APIStatusError as e:
        raise AIError(f"Claude API error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise AIError("Could not reach the Claude API (network).")
    if resp.stop_reason == "refusal":
        raise AIError("Claude declined this research request. Rephrase and retry.")
    if resp.stop_reason == "max_tokens":
        raise AIError("The research output was cut off. Narrow the scope and retry.")
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return parse_json(text), resp.model, _sources(content), True
