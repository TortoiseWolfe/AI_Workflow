#!/usr/bin/env python3
"""Turn the local usage ledger into the aggregate input that collect_gauges.py reads.

    read_local_ledger.py --output PATH [--now ISO] [--hub-scripts DIR] [--db PATH] [--copilot-db PATH]

Read-only. It reuses the existing readers rather than copying them: the ledger
database (opened mode=ro) and the context-load helpers of model_quality_report.py.
Only counts, token numbers and timestamps leave this script. Repo names, session
ids and file paths are read to join rows and are never written. Write the output
outside any repo: it is an intermediate file, not the published one.

A source with no reader yet (Codex session context, provider consoles)
is left null so the page says so, never filled with a guess.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import os
import sqlite3
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_codex_sessions

HOME = Path.home()
DEFAULT_HUB_SCRIPTS = HOME / "repos" / "hub" / "scripts"
DEFAULT_DB = HOME / ".local" / "share" / "ledger" / "ledger.db"
DEFAULT_COPILOT_DB = HOME / ".copilot" / "session-store.db"
CLAUDE_SCRIPTS = HOME / ".claude" / "scripts"
COPILOT_USAGE_ENDPOINT = "users/TortoiseWolfe/settings/billing/premium_request/usage"

# Review-panel experts in the ledger, folded onto the dial that carries their free tier.
EXPERT_TO_DIAL = {
    "gemini": "gemini",
    "groq": "groq",
    "groq_qwen": "groq",
    "cloudflare": "cloudflare-workers-ai",
    "openrouter": "openrouter",
    "antigravity": "antigravity",
    "local": "ollama",
}
CLAUDE_DIALS = {"opus": "claude-opus", "sonnet": "claude-sonnet", "haiku": "claude-haiku", "fable": "claude-fable"}
ALL_ENGINES = ("claude-opus", "claude-sonnet", "claude-haiku", "claude-fable", "codex", "copilot")
EMPTY = {
    "window_turns": None, "tokens_per_turn_median": None, "tokens_per_turn_p90": None,
    "turns_over_200k": None, "compactions_total": None, "compactions_auto": None,
    "compactions_manual": None, "reread_share": None, "input_tokens_per_call_median": None,
}


def load_reader(hub_scripts: Path):
    spec = importlib.util.spec_from_file_location("model_quality_report", hub_scripts / "model_quality_report.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["model_quality_report"] = module
    spec.loader.exec_module(module)
    return module


def iso(epoch: float) -> str:
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def provider_calls(conn) -> list[dict]:
    rows = conn.execute("SELECT ts, expert, input_tokens FROM panel").fetchall()
    calls = []
    for ts, expert, input_tokens in rows:
        dial = EXPERT_TO_DIAL.get(expert)
        if dial is None:
            continue
        seconds = ts / 1000 if ts > 1e12 else ts
        calls.append({
            "timestamp": iso(seconds), "provider_id": dial, "units": 1,
            # A panel row with 0 input tokens means the count was not recorded.
            "input_tokens": input_tokens if input_tokens else None,
            # Groq refills each model's budget separately, so the expert names the budget.
            "bucket": expert if dial == "groq" else None,
        })
    return sorted(calls, key=lambda call: call["timestamp"])


def _when(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc)


def claude_weekly_check(calibration: dict) -> dict | None:
    """Predict Claude's latest /usage reading from the earlier ones, so the check is not the fit's own data.

    The weekly estimate is a least-squares line through the origin over /usage readings. Refit without the
    newest reading and ask what it would have said for that reading's use; the gap is the honest error.
    """
    try:
        readings = sorted(calibration["readings"], key=lambda row: _when(row["at"]))
        *earlier, latest = readings
        if not earlier:
            return None
        weights = [float(row["weighted"]) for row in earlier]
        factor = sum(float(row["pct"]) * w for row, w in zip(earlier, weights)) / sum(w * w for w in weights)
        return {
            "at": iso(_when(latest["at"]).timestamp()),
            "theirs": float(latest["pct"]),
            "ours": round(factor * float(latest["weighted"]), 1),
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def claude_weekly(reader, ledger, now: dt.datetime, week_start, ingested: float, calibration_path=None) -> dict | None:
    """The shared weekly limit and each model's slice of it, from the hub's own projection (model_quality_report.py)."""
    calibration = reader.load_calibration(str(calibration_path or reader.DEFAULT_CAL))
    if calibration is None:
        return None
    projection = reader.project(ledger, now, calibration, week_start)
    factor = float(calibration["pct_per_unit"])
    by_family = {name: 0.0 for name in CLAUDE_DIALS}
    for _repo, model, *values in ledger._rows(week_start.timestamp(), now.timestamp()):
        family = reader.family(model)
        if family in by_family:
            by_family[family] += reader.weighted(model, *values, cache_w=reader.LIMIT_CACHE_READ_WEIGHT)
    stale = reader.calibration_note(calibration, now) is not None
    return {
        "as_of": iso(ingested),
        "limit": round(projection["implied_limit_units"]),
        "reset": iso(projection["reset"].timestamp()),
        "by_family": {name: round(units) for name, units in by_family.items()},
        "check": None if stale else claude_weekly_check(calibration),
    }


def claude_engines(reader, ledger, lo: float, hi: float, project_glob: str) -> dict[str, dict]:
    scale = ledger.scale
    rows = ledger.conn.execute(
        "SELECT message_id, model, COALESCE(input,0)+COALESCE(cache_5m,0)+COALESCE(cache_1h,0)+COALESCE(cache_read,0),"
        " COALESCE(cache_read,0) FROM tokens WHERE ts>=? AND ts<?",
        (int(lo * scale), int(hi * scale))).fetchall()
    contexts: dict[str, list[int]] = defaultdict(list)
    cached: dict[str, int] = defaultdict(int)
    total_in: dict[str, int] = defaultdict(int)
    family_of_message = {}
    for message_id, model, context, cache_read in rows:
        fam = reader.family(model)
        family_of_message[message_id] = fam
        contexts[fam].append(int(context))
        cached[fam] += int(cache_read)
        total_in[fam] += int(context)

    _projects, events = reader._transcript_metadata(project_glob, lo, hi)
    compactions: dict[str, dict[str, int]] = defaultdict(lambda: {"auto": 0, "manual": 0})
    for event in events:
        fam = family_of_message.get(event.get("previous_message_id"))
        if fam is None or event["kind"] not in ("auto", "manual"):
            continue  # cannot be attributed to a tier: leave it out rather than guess
        compactions[fam][event["kind"]] += 1

    out = {}
    for fam, dial in CLAUDE_DIALS.items():
        values = contexts.get(fam)
        if not values:
            continue
        auto, manual = compactions[fam]["auto"], compactions[fam]["manual"]
        out[dial] = {
            "window_turns": len(values),
            "tokens_per_turn_median": statistics.median(values),
            "tokens_per_turn_p90": reader.percentile(values, 0.9),
            "turns_over_200k": sum(value > 200_000 for value in values),
            "compactions_total": auto + manual, "compactions_auto": auto, "compactions_manual": manual,
            "reread_share": round(cached[fam] / total_in[fam], 3) if total_in[fam] else None,
            "input_tokens_per_call_median": None,
        }
    return out


def copilot_engine(db: Path, now: dt.datetime, reader) -> tuple[dict | None, str | None]:
    week_start = reader.week_start_for(now)
    uri = f"{db.resolve().as_uri()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=1)
    except sqlite3.OperationalError as error:
        return None, copilot_database_error(error)

    try:
        rows = conn.execute(
            "SELECT COALESCE(input_tokens, 0)+COALESCE(cache_read_tokens, 0)+"
            "COALESCE(cache_write_tokens, 0), COALESCE(request_multiplier, 1) "
            "FROM assistant_usage_events "
            "WHERE julianday(created_at)>=julianday(?) AND julianday(created_at)<julianday(?)",
            (week_start.isoformat(), (now + timedelta(seconds=1)).isoformat()),
        ).fetchall()
    except sqlite3.OperationalError as error:
        reason = copilot_database_error(error)
        if reason is None:
            raise
        return None, reason
    finally:
        conn.close()

    contexts = [int(row[0]) for row in rows]
    return {
        "used": sum(float(row[1]) for row in rows),
        "window_turns": len(contexts),
        "tokens_per_turn_median": statistics.median(contexts) if contexts else None,
        "tokens_per_turn_p90": reader.percentile(contexts, 0.9) if contexts else None,
        "turns_over_200k": sum(value > 200_000 for value in contexts),
        "compactions_total": None,
        "compactions_auto": None,
        "compactions_manual": None,
        "reread_share": None,
        "input_tokens_per_call_median": None,
    }, None


def copilot_database_error(error: sqlite3.OperationalError) -> str | None:
    message = str(error).lower()
    if "locked" in message or "busy" in message:
        return "local-database-locked"
    if "unable to open database file" in message:
        return "local-database-unavailable"
    return None


def premium_request_usage(now: dt.datetime, week_start: dt.datetime) -> tuple[float | None, str | None]:
    total = 0.0
    day = week_start
    while day.date() <= now.date():
        query = urlencode({
            "year": day.year, "month": day.month, "day": day.day, "product": "Copilot",
        })
        try:
            result = subprocess.run(
                ["gh", "api", f"{COPILOT_USAGE_ENDPOINT}?{query}"],
                capture_output=True, text=True, timeout=30, check=False,
            )
        except FileNotFoundError:
            return None, "gh-cli-unavailable"
        except subprocess.TimeoutExpired:
            return None, "github-report-unavailable"
        if result.returncode:
            if "404" in result.stderr:
                return None, "github-report-404-user-scope"
            return None, "github-report-unavailable"
        try:
            response = json.loads(result.stdout)
            items = response["usageItems"]
            if not isinstance(items, list):
                raise ValueError
            for item in items:
                amount = item["grossQuantity"]
                if (
                    isinstance(amount, bool)
                    or not isinstance(amount, (int, float))
                    or not math.isfinite(amount)
                    or amount < 0
                ):
                    raise ValueError
                product = item.get("product")
                if product is not None and not isinstance(product, str):
                    raise ValueError
                if product is not None and product.casefold() != "copilot":
                    continue
                total += float(amount)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None, "github-report-invalid"
        day += timedelta(days=1)
    return total, None


def probe_groq(now: dt.datetime, scripts: Path = CLAUDE_SCRIPTS) -> dict | None:
    """Read Groq's own request count; log each probe to the usage ledger so both sides count it."""
    import read_groq_limits

    logger = scripts / "ledger_log.py"
    if not logger.is_file():
        return None
    spec = importlib.util.spec_from_file_location("ledger_log", logger)
    ledger_log = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger_log)
    models = dict(read_groq_limits.MODELS)

    def log(expert: str) -> None:
        ledger_log.append(ledger_log.record(
            "AI_Workflow", expert, models[expert], 0, 0, 0, "public", "gauge-probe"))

    report = read_groq_limits.groq_report(now, log=log)
    if report is not None:
        subprocess.run(
            [sys.executable, str(scripts / "usage_ledger.py"), "ingest", "--quiet"],
            capture_output=True, timeout=120, check=False,
        )
    return report


def build_input(
    reader, db: Path, now: dt.datetime, copilot_db: Path = DEFAULT_COPILOT_DB, groq_probe=None,
    claude_calibration=None, codex_sessions: Path = read_codex_sessions.SESSIONS,
) -> dict:
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    now = now.astimezone(dt.timezone.utc)
    groq_row = groq_probe(now) if groq_probe else None
    conn = reader.open_ro(str(db))
    ledger = reader.Ledger(conn)
    last_row = ledger.last_ts()
    meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    ingested = float(meta["last_ingest"]) if meta.get("last_ingest") else None
    if last_row is None or ingested is None:
        raise SystemExit("the ledger has no rows or no ingest time; refusing to publish a guess")
    week_start = reader.week_start_for(now)
    measured = claude_engines(reader, ledger, week_start.timestamp(), now.timestamp() + 1, reader.DEFAULT_PROJECT_GLOB)
    copilot, local_error = copilot_engine(copilot_db, now, reader)
    report_used, report_error = (None, local_error)
    if copilot is not None:
        report_used, report_error = premium_request_usage(now, week_start)
    engines = []
    for engine_id in ALL_ENGINES:
        reading = measured.get(engine_id)
        if engine_id == "copilot" and copilot is not None:
            # the request count travels in copilot_report.local_used, not in the engine row
            reading = {key: value for key, value in copilot.items() if key != "used"}
        engines.append({
            "id": engine_id,
            "as_of": iso(now.timestamp()) if engine_id == "copilot" and reading is not None
            else iso(ingested) if reading else None,
            **(reading or EMPTY),
        })
    return {
        "ledger_as_of": iso(ingested),
        "last_activity": iso(last_row),
        "calls": provider_calls(conn),
        "provider_reports": [groq_row] if groq_row else [],  # only Groq has a header reader so far
        "engines": engines,
        "claude_weekly": claude_weekly(reader, ledger, now, week_start, ingested, claude_calibration),
        "codex_report": read_codex_sessions.codex_report(now, week_start, codex_sessions),
        "copilot_report": {
            "local_used": copilot["used"] if copilot is not None else None,
            "reported_used": report_used,
            "as_of": iso(now.timestamp()) if report_used is not None else None,
            "reason": report_error,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--now", help="timezone-aware ISO timestamp, for repeatable runs")
    parser.add_argument("--hub-scripts", type=Path, default=DEFAULT_HUB_SCRIPTS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--copilot-db", type=Path, default=DEFAULT_COPILOT_DB)
    args = parser.parse_args()
    now = dt.datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else dt.datetime.now(dt.timezone.utc)
    reader = load_reader(args.hub_scripts)
    payload = build_input(reader, args.db, now, args.copilot_db, groq_probe=probe_groq)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(args.output, 0o600)


if __name__ == "__main__":
    main()
