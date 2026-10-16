#!/usr/bin/env python3
"""Turn the local usage ledger into the aggregate input that collect_gauges.py reads.

    read_local_ledger.py --output PATH [--now ISO] [--hub-scripts DIR] [--db PATH]

Read-only. It reuses the existing readers rather than copying them: the ledger
database (opened mode=ro) and the context-load helpers of model_quality_report.py.
Only counts, token numbers and timestamps leave this script. Repo names, session
ids and file paths are read to join rows and are never written. Write the output
outside any repo: it is an intermediate file, not the published one.

A source with no reader yet (Codex and Copilot session context, provider consoles)
is left null so the page says so, never filled with a guess.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
DEFAULT_HUB_SCRIPTS = HOME / "repos" / "hub" / "scripts"
DEFAULT_DB = HOME / ".local" / "share" / "ledger" / "ledger.db"

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
        })
    return sorted(calls, key=lambda call: call["timestamp"])


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


def build_input(reader, db: Path, now: dt.datetime) -> dict:
    conn = reader.open_ro(str(db))
    ledger = reader.Ledger(conn)
    last_row = ledger.last_ts()
    meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    ingested = float(meta["last_ingest"]) if meta.get("last_ingest") else None
    if last_row is None or ingested is None:
        raise SystemExit("the ledger has no rows or no ingest time; refusing to publish a guess")
    week_start = reader.week_start_for(now)
    measured = claude_engines(reader, ledger, week_start.timestamp(), now.timestamp() + 1, reader.DEFAULT_PROJECT_GLOB)
    engines = []
    for engine_id in ALL_ENGINES:
        reading = measured.get(engine_id)
        engines.append({"id": engine_id, "as_of": iso(ingested) if reading else None, **(reading or EMPTY)})
    return {
        "ledger_as_of": iso(ingested),
        "last_activity": iso(last_row),
        "calls": provider_calls(conn),
        "provider_reports": [],  # no provider console or key-endpoint reader yet
        "engines": engines,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--now", help="timezone-aware ISO timestamp, for repeatable runs")
    parser.add_argument("--hub-scripts", type=Path, default=DEFAULT_HUB_SCRIPTS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    now = dt.datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else dt.datetime.now(dt.timezone.utc)
    reader = load_reader(args.hub_scripts)
    payload = build_input(reader, args.db, now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(args.output, 0o600)


if __name__ == "__main__":
    main()
