import copy
import datetime as dt
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collect_gauges
import read_codex_sessions
import read_local_ledger

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "gauge-input.json").read_text(encoding="utf-8"))
NOW = dt.datetime(2026, 10, 19, 15, 22, 40, tzinfo=dt.timezone.utc)
PAGE = (ROOT / "gauges.html").read_text(encoding="utf-8")


def z(moment):
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def groq_payload(calls, reported_used, as_of=NOW - dt.timedelta(seconds=37)):
    payload = copy.deepcopy(FIXTURE)
    payload["ledger_as_of"] = z(NOW - dt.timedelta(seconds=20))
    payload["last_activity"] = z(NOW - dt.timedelta(seconds=30))
    payload["calls"] = [c for c in payload["calls"] if c["provider_id"] != "groq"] + calls
    payload["provider_reports"] = [r for r in payload["provider_reports"] if r["provider_id"] != "groq"] + [{
        "provider_id": "groq", "as_of": z(as_of), "used": reported_used, "limit": 2000,
        "window_complete": True, "source": "provider", "resets_at": None, "refill_seconds": 86.4,
    }]
    for engine in payload["engines"]:
        engine["as_of"] = z(NOW - dt.timedelta(seconds=20)) if engine["as_of"] else None
    payload["copilot_report"] = {"local_used": None, "reported_used": None, "as_of": None, "reason": None}
    return payload


def call(moment, bucket):
    return {"timestamp": z(moment), "provider_id": "groq", "units": 1, "input_tokens": None, "bucket": bucket}


def dial(snapshot, dial_id):
    return next(item for item in snapshot["providers"] if item["id"] == dial_id)


class GroqLeakyBucketTests(unittest.TestCase):
    """Groq's budget refills one request per 86.4 s per model, so its 'used' is a bucket level, not a 24 h count."""

    def test_old_calls_have_drained_so_a_small_provider_count_matches_the_ledger(self):
        calls = [call(NOW - dt.timedelta(hours=8, seconds=i), bucket) for i in range(7) for bucket in ("groq", "groq_qwen")]
        calls += [call(NOW - dt.timedelta(seconds=36), "groq"), call(NOW - dt.timedelta(seconds=36), "groq_qwen")]
        snapshot = collect_gauges.build_snapshot(groq_payload(calls, 2), NOW)
        groq = dial(snapshot, "groq")
        self.assertEqual(groq["state"], "calibrated")
        self.assertEqual((groq["used"], groq["limit"], groq["percent"]), (2, 2000, 0.1))
        self.assertEqual(groq["cross_check"]["against"], "provider headers")
        self.assertEqual(groq["cross_check"]["theirs"], 2)
        self.assertLessEqual(abs(groq["cross_check"]["ours"] - 2), 2)
        self.assertTrue(groq["lit"])

    def test_a_burst_that_has_not_drained_must_still_be_in_the_provider_count(self):
        burst = [call(NOW - dt.timedelta(seconds=40 + i), bucket) for i in range(5) for bucket in ("groq", "groq_qwen")]
        matching = collect_gauges.build_snapshot(groq_payload(burst, 10), NOW)
        self.assertEqual(dial(matching, "groq")["state"], "calibrated")
        missing = collect_gauges.build_snapshot(groq_payload(burst, 2), NOW)
        self.assertEqual(dial(missing, "groq")["state"], "uncalibrated")
        self.assertIsNone(dial(missing, "groq")["cross_check"])
        self.assertFalse(dial(missing, "groq")["lit"])

    def test_a_mismatch_keeps_an_earlier_recorded_cross_check(self):
        burst = [call(NOW - dt.timedelta(seconds=40 + i), bucket) for i in range(5) for bucket in ("groq", "groq_qwen")]
        earlier = {"at": "2026-10-19T00:25:00Z", "against": "provider headers", "theirs": 10, "ours": 10}
        previous = {"providers": [{"id": "groq", "cross_check": earlier}]}
        snapshot = collect_gauges.build_snapshot(groq_payload(burst, 2), NOW, previous=previous)
        groq = dial(snapshot, "groq")
        self.assertEqual(groq["cross_check"], earlier)
        self.assertEqual(groq["state"], "calibrated")
        self.assertEqual(groq["percent"], 0.1)


class LitRuleTests(unittest.TestCase):
    def test_a_dial_with_no_limit_never_lights(self):
        snapshot = collect_gauges.build_snapshot(groq_payload([], 0), NOW)
        for item in snapshot["providers"]:
            if item["limit"] is None:
                self.assertFalse(item["lit"], item["id"])
                self.assertIsNone(item["percent"], item["id"])

    def test_lit_requires_a_fresh_reading(self):
        calls = [call(NOW - dt.timedelta(seconds=36), "groq"), call(NOW - dt.timedelta(seconds=36), "groq_qwen")]
        later = NOW + dt.timedelta(hours=17)
        payload = groq_payload(calls, 2)
        payload["last_activity"] = z(later - dt.timedelta(seconds=1))
        payload["ledger_as_of"] = z(later - dt.timedelta(seconds=1))
        snapshot = collect_gauges.build_snapshot(payload, later)
        self.assertFalse(dial(snapshot, "groq")["lit"])
        self.assertEqual(dial(snapshot, "groq")["state"], "stale")


class ClaudeWeeklyTests(unittest.TestCase):
    def payload(self, **overrides):
        payload = groq_payload([], 0)
        weekly = {
            "as_of": z(NOW - dt.timedelta(seconds=20)),
            "limit": 500_000_000,
            "reset": "2026-10-21T16:00:00Z",
            "by_family": {"opus": 250_000_000, "sonnet": 100_000_000, "haiku": 5_000_000, "fable": 50_000_000},
            "check": {"at": "2026-10-17T22:20:00Z", "theirs": 67.0, "ours": 68.9},
        }
        weekly.update(overrides)
        payload["claude_weekly"] = weekly
        return payload

    def test_each_model_dial_shows_its_slice_of_the_one_shared_limit(self):
        snapshot = collect_gauges.build_snapshot(self.payload(), NOW)
        shown = {name: dial(snapshot, f"claude-{name}") for name in ("opus", "sonnet", "haiku", "fable")}
        self.assertEqual([shown[n]["percent"] for n in shown], [50.0, 20.0, 1.0, 10.0])
        for item in shown.values():
            self.assertEqual(item["state"], "calibrated")
            self.assertEqual(item["limit"], 500_000_000)
            self.assertEqual(item["resets_at"], "2026-10-21T16:00:00Z")
            self.assertEqual(item["cross_check"]["against"], "Claude /usage")
            self.assertEqual(item["cross_check"]["at"], "2026-10-17T22:20:00Z")
            self.assertTrue(item["lit"])
            self.assertIn("one weekly limit", item["reason"])
            self.assertIn("81%", item["reason"])  # 250+100+5+50 of 500 M, all four together

    def test_a_check_that_misses_by_more_than_five_points_does_not_light_the_dials(self):
        bad = self.payload(check={"at": "2026-10-17T22:20:00Z", "theirs": 67.0, "ours": 80.0})
        snapshot = collect_gauges.build_snapshot(bad, NOW)
        self.assertEqual(dial(snapshot, "claude-opus")["state"], "uncalibrated")
        self.assertIsNone(dial(snapshot, "claude-opus")["percent"])
        self.assertFalse(dial(snapshot, "claude-opus")["lit"])

    def test_no_weekly_reading_leaves_the_dials_empty(self):
        payload = groq_payload([], 0)
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        self.assertIsNone(dial(snapshot, "claude-opus")["percent"])
        self.assertFalse(dial(snapshot, "claude-opus")["lit"])


class CodexTests(unittest.TestCase):
    def test_codex_count_is_published_without_a_percent(self):
        payload = groq_payload([], 0)
        payload["codex_report"] = {
            "as_of": z(NOW - dt.timedelta(seconds=20)), "used": 12345678,
            "provider_percent": 95.0, "provider_window_days": 30,
            "provider_as_of": "2026-10-14T19:53:56Z", "provider_resets_at": "2026-10-31T18:38:23Z",
        }
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        codex = dial(snapshot, "codex")
        self.assertEqual(codex["used"], 12345678)
        self.assertIsNone(codex["limit"])
        self.assertIsNone(codex["percent"])
        self.assertFalse(codex["lit"])
        self.assertIn("95", codex["reason"])
        self.assertIn("30", codex["reason"])


def write_session(directory: Path, name: str, events):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for stamp, total, last, rate in events:
            payload = {"type": "token_count", "info": None, "rate_limits": rate}
            if total is not None:
                payload["info"] = {"total_token_usage": {"total_tokens": total}, "last_token_usage": {"total_tokens": last}}
            handle.write(json.dumps({"timestamp": stamp, "type": "event_msg", "payload": payload}) + "\n")
        handle.write(json.dumps({"timestamp": "2026-10-15T00:00:00Z", "type": "response_item",
                                 "payload": {"type": "message", "content": "PRIVATE TEXT"}}) + "\n")


class CodexReaderTests(unittest.TestCase):
    def test_counts_only_this_weeks_tokens_and_repeated_events_once(self):
        since = dt.datetime(2026, 10, 14, 16, 0, tzinfo=dt.timezone.utc)
        rate = {"primary": {"used_percent": 95.0, "window_minutes": 43200, "resets_at": 1793471903}, "secondary": None}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_session(root, "2026/10/14/rollout-a.jsonl", [
                ("2026-10-14T15:00:00Z", 100, 100, None),            # before the week: left out
                ("2026-10-14T17:00:00Z", 300, 200, None),
                ("2026-10-14T17:00:01Z", 300, 200, None),            # same event emitted twice
                ("2026-10-14T19:53:56Z", 350, 50, rate),
            ])
            write_session(root, "2026/10/16/rollout-b.jsonl", [("2026-10-16T10:00:00Z", 40, 40, None)])
            report = read_codex_sessions.codex_report(NOW, since, root)
        self.assertEqual(report["used"], 290)
        self.assertEqual(report["provider_percent"], 95.0)
        self.assertEqual(report["provider_window_days"], 30)
        self.assertEqual(report["provider_as_of"], "2026-10-14T19:53:56Z")
        self.assertEqual(report["provider_resets_at"], "2026-10-31T18:38:23Z")
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_no_session_logs_means_no_report(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(read_codex_sessions.codex_report(NOW, NOW - dt.timedelta(days=7), Path(directory) / "none"))


class ClaudeWeeklyReaderTests(unittest.TestCase):
    def test_leave_one_out_check_predicts_the_latest_reading_from_the_others(self):
        calibration = {
            "readings": [
                {"pct": 80, "weighted": 419642177.0, "at": "2026-10-11T17:20-04:00"},
                {"pct": 88, "weighted": 433417046.0, "at": "2026-10-11T20:45-04:00"},
                {"pct": 41, "weighted": 215299994.0, "at": "2026-10-16T11:00-04:00"},
                {"pct": 67, "weighted": 350738192.0, "at": "2026-10-17T18:20-04:00"},
            ],
        }
        check = read_local_ledger.claude_weekly_check(calibration)
        self.assertEqual(check["theirs"], 67.0)
        self.assertAlmostEqual(check["ours"], 68.9, delta=0.2)
        self.assertEqual(check["at"], "2026-10-17T22:20:00Z")

    def test_a_single_reading_cannot_check_itself(self):
        self.assertIsNone(read_local_ledger.claude_weekly_check(
            {"readings": [{"pct": 67, "weighted": 1.0, "at": "2026-10-17T18:20-04:00"}]}))


class ClaudeWeeklyAssemblyTests(unittest.TestCase):
    def test_slices_use_the_limit_weighting_and_the_hubs_implied_limit(self):
        calibration = {"readings": [
            {"pct": 50, "weighted": 100.0, "at": "2026-10-10T12:00-04:00"},
            {"pct": 60, "weighted": 120.0, "at": "2026-10-11T12:00-04:00"},
        ]}

        class Ledger:
            @staticmethod
            def _rows(lo, hi):
                return [("repo-a", "claude-opus-5", 10, 5, 0, 0, 1000), ("repo-b", "claude-haiku-5", 20, 0, 0, 0, 0)]

        class Reader:
            LIMIT_CACHE_READ_WEIGHT = 0.0
            DEFAULT_CAL = "unused"
            load_calibration = staticmethod(lambda path: {"pct_per_unit": 0.5, **calibration})
            calibration_note = staticmethod(lambda cal, now: None)
            project = staticmethod(lambda ledger, now, cal, ws: {
                "implied_limit_units": 200.0, "reset": dt.datetime(2026, 10, 21, 16, tzinfo=dt.timezone.utc)})
            family = staticmethod(lambda model: "opus" if "opus" in model else "haiku")
            weighted = staticmethod(lambda model, i, o, w5, w1, r, cache_w: (4 if "opus" in model else 1) * (i + o + cache_w * r))

        week_start = NOW - dt.timedelta(days=2)
        weekly = read_local_ledger.claude_weekly(Reader, Ledger, NOW, week_start, NOW.timestamp(), None)
        self.assertEqual(weekly["limit"], 200)
        self.assertEqual(weekly["by_family"], {"opus": 60, "sonnet": 0, "haiku": 20, "fable": 0})  # cache reads ignored
        self.assertEqual(weekly["reset"], "2026-10-21T16:00:00Z")
        self.assertEqual(weekly["check"]["theirs"], 60.0)

    def test_no_calibration_file_means_no_weekly_figure(self):
        class Reader:
            DEFAULT_CAL = "unused"
            load_calibration = staticmethod(lambda path: None)

        self.assertIsNone(read_local_ledger.claude_weekly(Reader, None, NOW, NOW, 0, None))


class PageTests(unittest.TestCase):
    def test_legend_states_the_four_rules(self):
        for phrase in ("Source", "Limit", "Fresh", "Proven"):
            self.assertIn(f"<strong>{phrase}</strong>", PAGE)
        self.assertIn('id="legend"', PAGE)

    def test_each_dial_shows_its_source_and_last_cross_check(self):
        self.assertIn("Last cross-check", PAGE)
        self.assertIn("Source", PAGE)
        self.assertIn("cross_check", PAGE)

    def test_lamp_follows_lit_and_the_page_counts_lit_dials(self):
        self.assertIn("dial.lit", PAGE)
        self.assertIn('id="lit-count"', PAGE)


if __name__ == "__main__":
    unittest.main()
