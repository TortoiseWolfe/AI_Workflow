#!/usr/bin/env python3
"""Read Groq's own daily request count from its rate-limit response headers.

Groq sends x-ratelimit-limit-requests and x-ratelimit-remaining-requests (the
per-model requests-per-day budget) on every chat response, so one one-token call
per panel model gives the provider's count without a console login. The key is
read from its file inside this script and only ever goes in the Authorization
header; nothing from the request or the key is returned except two integers per
model.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

KEY_FILE = Path.home() / ".config" / "groq" / "api-key"
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODELS = (("groq", "openai/gpt-oss-120b"), ("groq_qwen", "qwen/qwen3.8-27b"))  # the panel's two Groq experts
TIMEOUT = 30


def _int_header(headers, name: str) -> int | None:
    value = headers.get(name)
    if value is None or not re.fullmatch(r"\d+", value.strip()):
        return None
    return int(value)


def probe_model(model: str, key: str, opener=urllib.request.urlopen):
    """One one-token call. -> (limit, remaining) or None."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ok"}],
        "max_completion_tokens": 1,
    }).encode()
    request = urllib.request.Request(ENDPOINT, body, {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "ai-workflow-gauges/1",
    })
    try:
        with opener(request, timeout=TIMEOUT) as response:
            headers = response.headers
    except urllib.error.HTTPError as error:
        headers = error.headers  # a 429 still carries the budget
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    limit = _int_header(headers, "x-ratelimit-limit-requests")
    remaining = _int_header(headers, "x-ratelimit-remaining-requests")
    if limit is None or remaining is None or limit <= 0 or remaining > limit:
        return None
    return limit, remaining


def groq_report(now: dt.datetime, key_file: Path = KEY_FILE, opener=urllib.request.urlopen, log=None):
    """-> provider_reports row, or None when any model could not be read.

    A probe is a real request, so Groq counts it. `log(expert)` is called once per
    successful probe so the usage ledger counts it too; the two sides then differ
    only by whatever else used the account.
    """
    try:
        key = key_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not key:
        return None
    used = limit = 0
    for expert, model in MODELS:
        reading = probe_model(model, key, opener)
        if reading is None:
            return None
        if log is not None:
            log(expert)
        model_limit, remaining = reading
        used += model_limit - remaining
        limit += model_limit
    stamp = now.astimezone(dt.timezone.utc)
    return {
        "provider_id": "groq",
        "as_of": stamp.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "used": used,
        "limit": limit,
        "window_complete": True,
        "source": "provider",
        "resets_at": None,  # the budget refills one request at a time (86.4 s each), so no single reset time
    }
