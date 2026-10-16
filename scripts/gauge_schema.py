"""Strict input and output contracts for the public aggregate gauge snapshot."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data" / "gauges.schema.json"

PROVIDERS = (
    ("gemini", "Gemini (AI Studio)", "daily", "requests", True),
    ("groq", "Groq", "daily", "requests", True),
    ("cloudflare-workers-ai", "Cloudflare Workers AI", "daily", "requests", True),
    ("openrouter", "OpenRouter free", "daily", "requests", True),
    ("antigravity", "Antigravity CLI", "weekly", "invocations", True),
    ("ollama", "Ollama (local, unlimited)", "rolling hour", "requests/hour", True),
    ("mistral", "Mistral Experiment", "monthly", "requests", False),
    ("sambanova", "SambaNova Cloud", "monthly", "requests", False),
    ("github-models", "GitHub Models", "monthly", "requests", False),
)
ENGINES = (
    ("claude-opus", "Claude Opus"),
    ("claude-sonnet", "Claude Sonnet"),
    ("claude-haiku", "Claude Haiku"),
    ("claude-fable", "Claude Fable"),
    ("codex", "Codex"),
    ("copilot", "Copilot"),
)
ENGINE_WINDOWS = {engine_id: "weekly" for engine_id, _ in ENGINES}
INPUT_ROOT_KEYS = {"ledger_as_of", "last_activity", "calls", "provider_reports", "engines"}
CALL_KEYS = {"timestamp", "provider_id", "units", "input_tokens"}
REPORT_KEYS = {"provider_id", "as_of", "used", "limit", "window_complete", "source", "resets_at"}
ENGINE_KEYS = {
    "id", "as_of", "window_turns", "tokens_per_turn_median", "tokens_per_turn_p90",
    "turns_over_200k", "compactions_total", "compactions_auto", "compactions_manual",
    "reread_share", "input_tokens_per_call_median",
}
CONTEXT_FIELDS = (
    "window_turns", "tokens_per_turn_median", "tokens_per_turn_p90", "turns_over_200k",
    "compactions_total", "compactions_auto", "compactions_manual", "reread_share",
    "input_tokens_per_call_median",
)
CONTEXT_GROUPS = {
    "turns": ("window_turns", "tokens_per_turn_median", "tokens_per_turn_p90", "turns_over_200k"),
    "compactions": ("compactions_total", "compactions_auto", "compactions_manual"),
    "reread": ("reread_share",),
    "input_tokens": ("input_tokens_per_call_median",),
}


class InputError(ValueError):
    """Raised when the local input has fields or values outside the narrow contract."""


def parse_time(value: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise InputError(f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InputError(f"{field} must be an ISO timestamp") from error
    if parsed.tzinfo is None:
        raise InputError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def number_or_none(value: Any, field: str, *, maximum: float | None = None) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise InputError(f"{field} must be a non-negative number or null")
    if maximum is not None and value > maximum:
        raise InputError(f"{field} must be at most {maximum}")
    return value


def exact_keys(value: Any, allowed: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{field} must be an object")
    extra = set(value) - allowed
    missing = allowed - set(value)
    if extra or missing:
        raise InputError(f"{field} has unsupported fields: extra={sorted(extra)}, missing={sorted(missing)}")
    return value


def load_catalog() -> dict[str, dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    catalog = schema.get("x-provider-weight-rationales")
    if not isinstance(catalog, dict):
        raise InputError("provider weight rationales are missing from the schema")
    if set(catalog) != {row[0] for row in PROVIDERS}:
        raise InputError("provider weight rationales do not match the configured dials")
    for provider_id, rationale in catalog.items():
        if (
            not isinstance(rationale, dict)
            or set(rationale) != {"weight", "reason"}
            or rationale["weight"] not in ("small", "medium", "large")
            or not isinstance(rationale["reason"], str)
            or not rationale["reason"].strip()
        ):
            raise InputError(f"provider weight rationale is invalid for {provider_id}")
    return catalog


def window_start(window: str, now: datetime) -> datetime:
    if window == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if window == "monthly":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if window == "weekly":
        start = now - timedelta(days=now.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    return now - timedelta(hours=1)


def validate_input(payload: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], datetime, datetime]:
    root = exact_keys(payload, INPUT_ROOT_KEYS, "input")
    ledger_as_of = parse_time(root["ledger_as_of"], "ledger_as_of")
    last_activity = parse_time(root["last_activity"], "last_activity")
    calls = root["calls"]
    reports = root["provider_reports"]
    engines = root["engines"]
    if not all(isinstance(rows, list) for rows in (calls, reports, engines)):
        raise InputError("calls, provider_reports and engines must be arrays")
    provider_ids = {row[0] for row in PROVIDERS}
    engine_ids = {row[0] for row in ENGINES}
    clean_calls: list[dict[str, Any]] = []
    for index, raw in enumerate(calls):
        call = exact_keys(raw, CALL_KEYS, f"calls[{index}]")
        if not isinstance(call["provider_id"], str) or call["provider_id"] not in provider_ids:
            raise InputError(f"calls[{index}].provider_id is not recognized")
        units = number_or_none(call["units"], f"calls[{index}].units")
        if units is None:
            raise InputError(f"calls[{index}].units cannot be null")
        clean_calls.append({
            "timestamp": parse_time(call["timestamp"], f"calls[{index}].timestamp"),
            "provider_id": call["provider_id"],
            "units": units,
            "input_tokens": number_or_none(call["input_tokens"], f"calls[{index}].input_tokens"),
        })

    clean_reports: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(reports):
        report = exact_keys(raw, REPORT_KEYS, f"provider_reports[{index}]")
        provider_id = report["provider_id"]
        if not isinstance(provider_id, str) or provider_id not in provider_ids or provider_id in clean_reports:
            raise InputError(f"provider_reports[{index}].provider_id is invalid or duplicated")
        if report["source"] not in ("provider", "local-count"):
            raise InputError(f"provider_reports[{index}].source is not recognized")
        if not isinstance(report["window_complete"], bool):
            raise InputError(f"provider_reports[{index}].window_complete must be boolean")
        used = number_or_none(report["used"], f"provider_reports[{index}].used")
        limit = number_or_none(report["limit"], f"provider_reports[{index}].limit")
        if limit == 0:
            raise InputError(f"provider_reports[{index}].limit must be greater than zero")
        clean_reports[provider_id] = {
            **report,
            "as_of": parse_time(report["as_of"], f"provider_reports[{index}].as_of"),
            "used": used,
            "limit": limit,
            "resets_at": (
                parse_time(report["resets_at"], f"provider_reports[{index}].resets_at")
                if report["resets_at"] is not None else None
            ),
        }

    clean_engines: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(engines):
        engine = exact_keys(raw, ENGINE_KEYS, f"engines[{index}]")
        engine_id = engine["id"]
        if not isinstance(engine_id, str) or engine_id not in engine_ids or engine_id in clean_engines:
            raise InputError(f"engines[{index}].id is invalid or duplicated")
        fields = {
            field: number_or_none(
                engine[field], f"engines[{index}].{field}",
                maximum=1 if field == "reread_share" else None,
            )
            for field in CONTEXT_FIELDS
        }
        for field in ("window_turns", "turns_over_200k", "compactions_total", "compactions_auto", "compactions_manual"):
            value = fields[field]
            if value is not None and not float(value).is_integer():
                raise InputError(f"engines[{index}].{field} must be an integer count")
        compaction_parts = (fields["compactions_auto"], fields["compactions_manual"])
        if fields["compactions_total"] is None:
            if any(value is not None for value in compaction_parts):
                raise InputError(f"engines[{index}] cannot split an unknown compaction total")
        elif any(value is None for value in compaction_parts) or sum(compaction_parts) != fields["compactions_total"]:
            raise InputError(f"engines[{index}] compaction total must equal its auto and manual counts")
        clean_engines[engine_id] = {
            **fields,
            "as_of": parse_time(engine["as_of"], f"engines[{index}].as_of")
            if engine["as_of"] is not None else None,
        }
    return clean_calls, clean_reports, clean_engines, ledger_as_of, last_activity


def validate_snapshot(snapshot: Any) -> None:
    root = exact_keys(snapshot, {"generated_at", "activity", "providers"}, "snapshot")
    parse_time(root["generated_at"], "generated_at")
    if root["activity"] not in ("idle", "working"):
        raise InputError("activity is not recognized")
    if not isinstance(root["providers"], list) or len(root["providers"]) != 15:
        raise InputError("snapshot must contain exactly 15 dials")
    catalog = load_catalog()
    known = {row[0]: (row[1], "free-tier", row[2], row[3], row[4]) for row in PROVIDERS}
    known.update({
        engine_id: (display_name, "engine", ENGINE_WINDOWS[engine_id], "tokens", True)
        for engine_id, display_name in ENGINES
    })
    seen = set()
    allowed = {
        "as_of", "id", "display_name", "kind", "window", "weight", "used", "limit",
        "unit", "percent", "state", "resets_at", "source", "context", "context_state",
    }
    context_keys = set(CONTEXT_FIELDS)
    group_keys = set(CONTEXT_GROUPS)
    for index, raw in enumerate(root["providers"]):
        dial = exact_keys(raw, allowed, f"providers[{index}]")
        if not isinstance(dial["id"], str) or dial["id"] not in known or dial["id"] in seen:
            raise InputError(f"providers[{index}].id is unknown or duplicated")
        seen.add(dial["id"])
        expected_name, expected_kind, expected_window, expected_unit, claimed = known[dial["id"]]
        if (dial["display_name"], dial["kind"], dial["window"], dial["unit"]) != (
            expected_name, expected_kind, expected_window, expected_unit
        ):
            raise InputError(f"providers[{index}] contains unknown public labels")
        if dial["weight"] != (catalog[dial["id"]]["weight"] if expected_kind == "free-tier" else "medium"):
            raise InputError(f"providers[{index}].weight does not match the schema")
        if dial["state"] not in ("calibrated", "uncalibrated", "stale", "idle", "unclaimed"):
            raise InputError(f"providers[{index}].state is invalid")
        if dial["source"] not in ("provider", "local-count"):
            raise InputError(f"providers[{index}].source is invalid")
        if (not claimed and dial["state"] != "unclaimed") or (claimed and dial["state"] == "unclaimed"):
            raise InputError("provider claim state does not match the configured dial")
        exact_keys(dial["context"], context_keys, f"providers[{index}].context")
        exact_keys(dial["context_state"], group_keys, f"providers[{index}].context_state")
        for field in context_keys:
            number_or_none(
                dial["context"][field], f"providers[{index}].context.{field}",
                maximum=1 if field == "reread_share" else None,
            )
        for field, value in dial["context_state"].items():
            if value not in ("calibrated", "uncalibrated", "not-applicable"):
                raise InputError(f"providers[{index}].context_state.{field} is invalid")
        for field in ("used", "limit", "percent"):
            number_or_none(dial[field], f"providers[{index}].{field}")
        for field in ("as_of", "resets_at"):
            if dial[field] is not None:
                parse_time(dial[field], f"providers[{index}].{field}")
        if dial["state"] != "calibrated" and dial["percent"] is not None:
            raise InputError("uncalibrated or stale dials cannot publish a percentage")
        if dial["percent"] is not None:
            if dial["limit"] is None or dial["limit"] == 0 or dial["used"] is None:
                raise InputError("a percentage requires used and limit values")
            expected_percent = round(float(dial["used"]) / dial["limit"] * 100, 1)
            if dial["percent"] != expected_percent:
                raise InputError("percentage does not match the published values")
    if seen != set(known):
        raise InputError("snapshot is missing a known dial")
