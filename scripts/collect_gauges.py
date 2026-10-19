#!/usr/bin/env python3
"""Build the public aggregate snapshot from strict local aggregate JSON (read_local_ledger.py output or a fixture)."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from gauge_schema import (
    CONTEXT_FIELDS,
    CONTEXT_GROUPS,
    ENGINES,
    ENGINE_UNITS,
    PROVIDERS,
    InputError,
    load_catalog,
    parse_time,
    validate_input,
    validate_snapshot,
    window_start,
)

IDLE_AFTER = timedelta(days=7)
REFRESH_INTERVAL = timedelta(hours=8)
STALE_AFTER = 2 * REFRESH_INTERVAL
ACTIVE_WITHIN = timedelta(hours=1)
MIN_COMPACTIONS_TO_PUBLISH = 20


def _context_for_engine(engine: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, str]]:
    context = {field: None for field in CONTEXT_FIELDS}
    states = {group: "uncalibrated" for group in CONTEXT_GROUPS}
    states["input_tokens"] = "not-applicable"
    if engine is None:
        return context, states
    context.update(engine)
    context.pop("as_of", None)
    total = engine["compactions_total"]
    if total is not None and total < MIN_COMPACTIONS_TO_PUBLISH:
        for field in CONTEXT_GROUPS["compactions"]:
            context[field] = None
    # Every group stays "uncalibrated" until a hand-counted sample confirms it (FR-009, FR-030).
    return context, states


def build_snapshot(payload: Any, now: datetime) -> dict[str, Any]:
    if now.tzinfo is None:
        raise InputError("now must include a timezone")
    now = now.astimezone(timezone.utc)
    calls, reports, engines, ledger_as_of, last_activity, copilot_report = validate_input(payload)
    if any(call["timestamp"] > now for call in calls):
        raise InputError("calls cannot be dated in the future")
    if any(report["as_of"] > now for report in reports.values()):
        raise InputError("provider reports cannot be dated in the future")
    if any(engine["as_of"] and engine["as_of"] > now for engine in engines.values()):
        raise InputError("engine readings cannot be dated in the future")
    if copilot_report["as_of"] and copilot_report["as_of"] > now:
        raise InputError("copilot report cannot be dated in the future")
    if ledger_as_of > now or last_activity > now:
        raise InputError("ledger times cannot be in the future")

    weights = load_catalog()
    dials = []
    recent_activity = now - last_activity <= ACTIVE_WITHIN
    for provider_id, name, window, unit, claimed in PROVIDERS:
        start = window_start(window, now)
        relevant = [call for call in calls if call["provider_id"] == provider_id]
        current = [call for call in relevant if start <= call["timestamp"] <= now]
        local_used = sum(call["units"] for call in current)
        token_counts = [call["input_tokens"] for call in current if call["input_tokens"] is not None]
        token_median = statistics.median(token_counts) if token_counts else None
        last_call = max((call["timestamp"] for call in relevant), default=None)

        report = reports.get(provider_id)
        # A local count was read when the ledger was; a quiet provider is not a stale one.
        source, used, limit, resets_at, as_of = "local-count", local_used, None, None, ledger_as_of
        state = "unclaimed" if not claimed else "uncalibrated"
        percent = None
        if not claimed:
            used = 0
        elif last_call and now - last_call > IDLE_AFTER:
            state, as_of = "idle", last_call  # as_of doubles as "idle since"
        elif report:
            source, as_of, resets_at = report["source"], report["as_of"], report["resets_at"]
            limit = report["limit"]
            report_used = report["used"]
            if report["window_complete"] and report_used is not None and limit is not None:
                tolerance = max(2, report_used * 0.05)
                if abs(local_used - report_used) <= tolerance:
                    state = "calibrated"
                    if source == "provider":
                        used = report_used
                    percent = round(float(used) / limit * 100, 1)
        if claimed and state not in ("idle", "unclaimed") and as_of and now - as_of > STALE_AFTER:
            state, percent = "stale", None

        dials.append({
            "as_of": as_of.isoformat(timespec="seconds").replace("+00:00", "Z") if as_of else None,
            "id": provider_id,
            "display_name": name,
            "kind": "free-tier",
            "window": window,
            "weight": weights[provider_id]["weight"],
            "used": used,
            "limit": limit,
            "unit": unit,
            "percent": percent,
            "state": state,
            "resets_at": resets_at.isoformat(timespec="seconds").replace("+00:00", "Z") if resets_at else None,
            "source": source,
            "context": {
                **{field: None for field in CONTEXT_FIELDS},
                "input_tokens_per_call_median": token_median,
            },
            "context_state": {
                "turns": "not-applicable",
                "compactions": "not-applicable",
                "reread": "not-applicable",
                "input_tokens": "uncalibrated",
            },
        })

    for engine_id, name in ENGINES:
        engine = engines.get(engine_id)
        context, context_state = _context_for_engine(engine)
        as_of = engine["as_of"] if engine else None
        engine_state = "stale" if as_of and now - as_of > STALE_AFTER else "uncalibrated"
        dial = {
            "as_of": as_of.isoformat(timespec="seconds").replace("+00:00", "Z") if as_of else None,
            "id": engine_id,
            "display_name": name,
            "kind": "engine",
            "window": "weekly",
            "weight": "medium",
            "used": copilot_report["local_used"] if engine_id == "copilot" else None,
            "limit": None,
            "unit": ENGINE_UNITS[engine_id],
            "percent": None,
            "state": engine_state,
            "resets_at": None,
            "source": "local-count",
            "context": context,
            "context_state": context_state,
        }
        if engine_id == "copilot":
            reason = {
                "local-database-unavailable": "Local Copilot usage database is missing or unreadable.",
                "local-database-locked": "Local Copilot usage database is locked; no local count was read.",
                "gh-cli-unavailable": "GitHub CLI is unavailable; premium-request usage was not checked.",
                "github-report-404-user-scope": "GitHub premium-request usage returned 404; the gh token needs the user scope.",
                "github-report-unavailable": "GitHub premium-request usage report is unavailable.",
                "github-report-invalid": "GitHub premium-request usage report had an unsupported response.",
            }.get(copilot_report["reason"])
            if (
                copilot_report["local_used"] is not None
                and copilot_report["reported_used"] is not None
                and copilot_report["as_of"] is not None
            ):
                report_used = copilot_report["reported_used"]
                tolerance = max(copilot_report["local_used"], report_used) * 0.05
                if abs(copilot_report["local_used"] - report_used) <= tolerance:
                    dial["state"] = "calibrated"
                    reason = None
                else:
                    reason = "GitHub premium-request usage differs from the local count by more than 5%."
            dial["reason"] = reason
        dials.append(dial)

    snapshot = {
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "activity": "working" if recent_activity else "idle",
        "providers": dials,
    }
    validate_snapshot(snapshot)
    return snapshot


def write_snapshot(snapshot: dict[str, Any], output_path: Path) -> None:
    validate_snapshot(snapshot)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{output_path.name}.", dir=output_path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(snapshot, file, indent=2, ensure_ascii=True)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, output_path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="aggregate JSON input, from read_local_ledger.py or a fixture")
    parser.add_argument("--output", required=True, type=Path, help="destination for the allowlisted snapshot")
    parser.add_argument("--now", help="optional timezone-aware ISO timestamp for repeatable tests")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    now = parse_time(args.now, "--now") if args.now else datetime.now(timezone.utc)
    write_snapshot(build_snapshot(payload, now), args.output)


if __name__ == "__main__":
    main()
