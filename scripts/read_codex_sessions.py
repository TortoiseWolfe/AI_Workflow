#!/usr/bin/env python3
"""Count Codex tokens from its own session logs.

Codex writes one JSONL file per session under ~/.codex/sessions. Only the
token_count events are read: each carries the tokens of one model turn and,
now and then, the provider's own rate-limit figure. Message text is never
parsed into the result; only numbers and timestamps leave this script.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

SESSIONS = Path.home() / ".codex" / "sessions"


def _stamp(value: str) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return parsed if parsed.tzinfo else None


def _z(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _whole(value) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return None
    return int(value)


def codex_report(now: dt.datetime, since: dt.datetime, sessions: Path = SESSIONS) -> dict | None:
    """-> codex_report row (tokens since `since`, and the provider's last rate-limit figure) or None."""
    if not sessions.is_dir():
        return None
    used = 0
    files = 0
    newest_limit: tuple[dt.datetime, dict] | None = None
    for path in sorted(sessions.rglob("*.jsonl")):
        seen: set[int] = set()
        try:
            handle = path.open(encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                if "token_count" not in line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = event.get("payload") if isinstance(event, dict) else None
                if not isinstance(payload, dict) or payload.get("type") != "token_count":
                    continue
                when = _stamp(event.get("timestamp"))
                if when is None or when > now:
                    continue
                limits = payload.get("rate_limits")
                primary = limits.get("primary") if isinstance(limits, dict) else None
                if isinstance(primary, dict) and (newest_limit is None or when > newest_limit[0]):
                    newest_limit = (when, primary)
                info = payload.get("info")
                if not isinstance(info, dict) or when < since:
                    continue
                cumulative = _whole((info.get("total_token_usage") or {}).get("total_tokens"))
                turn = _whole((info.get("last_token_usage") or {}).get("total_tokens"))
                if cumulative is None or turn is None or cumulative in seen:
                    continue  # the same turn is logged more than once
                seen.add(cumulative)
                used += turn
                files += 1
    if files == 0 and newest_limit is None:
        return None
    report = {
        "as_of": _z(now), "used": used,
        "provider_percent": None, "provider_window_days": None,
        "provider_as_of": None, "provider_resets_at": None,
    }
    if newest_limit is not None:
        when, primary = newest_limit
        percent, minutes, resets = primary.get("used_percent"), _whole(primary.get("window_minutes")), _whole(primary.get("resets_at"))
        if isinstance(percent, (int, float)) and not isinstance(percent, bool) and 0 <= percent <= 1000:
            report["provider_percent"] = float(percent)
            report["provider_as_of"] = _z(when)
            report["provider_window_days"] = round(minutes / 1440) if minutes else None
            if resets:
                report["provider_resets_at"] = _z(dt.datetime.fromtimestamp(resets, dt.timezone.utc))
    return report
