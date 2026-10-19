import json
import math
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import read_local_ledger

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


class ReaderHelpers:
    @staticmethod
    def week_start_for(now):
        start = now - timedelta(days=now.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def percentile(values, fraction):
        ordered = sorted(values)
        return ordered[min(math.ceil(fraction * len(ordered)) - 1, len(ordered) - 1)]


class CopilotReaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.db = Path(self.temporary.name) / "session-store.db"
        connection = sqlite3.connect(self.db)
        try:
            schema = (ROOT / "tests" / "fixtures" / "copilot-store-schema.sql").read_text()
            connection.executescript(schema)
            connection.execute(
                "INSERT INTO sessions (id) VALUES (?)",
                ("fixture-session",),
            )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self):
        self.temporary.cleanup()

    def add_event(self, created_at, input_tokens, cache_read=0, cache_write=0, multiplier=1):
        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "INSERT INTO assistant_usage_events "
                "(session_id, model, input_tokens, cache_read_tokens, cache_write_tokens, "
                "output_tokens, reasoning_tokens, request_multiplier, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("fixture-session", "fixture-model", input_tokens, cache_read, cache_write, 7, 2, multiplier, created_at),
            )
            connection.commit()
        finally:
            connection.close()

    def test_normal_week_counts_requests_and_input_context(self):
        self.add_event("2026-10-12 00:00:00", 10, cache_read=2, cache_write=3, multiplier=1)
        self.add_event("2026-10-14 08:30:00", 200_000, cache_read=100, multiplier=2)
        self.add_event("2026-10-17 11:59:59", 20, multiplier=0.5)
        self.add_event("2026-10-11 23:59:59", 99_999)
        self.add_event("2026-10-18 00:00:00", 99_999)

        reading, error = read_local_ledger.copilot_engine(self.db, NOW, ReaderHelpers)

        self.assertIsNone(error)
        self.assertEqual(reading["used"], 3.5)
        self.assertEqual(reading["window_turns"], 3)
        self.assertEqual(reading["tokens_per_turn_median"], 20)
        self.assertEqual(reading["tokens_per_turn_p90"], 200_100)
        self.assertEqual(reading["turns_over_200k"], 1)
        self.assertIsNone(reading["compactions_total"])

    def test_empty_table_has_zero_count_and_no_percentiles(self):
        reading, error = read_local_ledger.copilot_engine(self.db, NOW, ReaderHelpers)

        self.assertIsNone(error)
        self.assertEqual(reading["used"], 0)
        self.assertEqual(reading["window_turns"], 0)
        self.assertIsNone(reading["tokens_per_turn_median"])
        self.assertIsNone(reading["tokens_per_turn_p90"])
        self.assertEqual(reading["turns_over_200k"], 0)

    def test_missing_database_leaves_no_reading(self):
        reading, error = read_local_ledger.copilot_engine(
            Path(self.temporary.name) / "missing.db", NOW, ReaderHelpers
        )

        self.assertIsNone(reading)
        self.assertEqual(error, "local-database-unavailable")

    def test_locked_database_leaves_no_reading(self):
        writer = sqlite3.connect(self.db)
        writer.execute("BEGIN EXCLUSIVE")
        try:
            reading, error = read_local_ledger.copilot_engine(self.db, NOW, ReaderHelpers)
        finally:
            writer.rollback()
            writer.close()

        self.assertIsNone(reading)
        self.assertEqual(error, "local-database-locked")

    @patch("read_local_ledger.subprocess.run")
    def test_premium_request_report_sums_requested_daily_quantities(self, run):
        run.return_value.returncode = 0
        run.return_value.stderr = ""
        run.return_value.stdout = json.dumps({
            "usageItems": [
                {"product": "Copilot", "grossQuantity": 2.5},
                {"product": "Other", "grossQuantity": 100},
            ]
        })

        total, error = read_local_ledger.premium_request_usage(
            NOW, ReaderHelpers.week_start_for(NOW)
        )

        self.assertEqual(total, 15)
        self.assertIsNone(error)
        self.assertEqual(run.call_count, 6)

    @patch("read_local_ledger.subprocess.run")
    def test_missing_user_scope_never_returns_a_calibration_count(self, run):
        run.return_value.returncode = 1
        run.return_value.stderr = "gh: Not Found (HTTP 404)"

        total, error = read_local_ledger.premium_request_usage(
            NOW, ReaderHelpers.week_start_for(NOW)
        )

        self.assertIsNone(total)
        self.assertEqual(error, "github-report-404-user-scope")
        self.assertEqual(run.call_count, 1)

    @patch("read_local_ledger.premium_request_usage", return_value=(None, "github-report-404-user-scope"))
    @patch("read_local_ledger.provider_calls", return_value=[])
    @patch("read_local_ledger.claude_engines", return_value={})
    def test_reader_output_is_accepted_by_the_collector(self, _engines, _calls, _usage):
        import collect_gauges

        self.add_event("2026-10-14 08:30:00", 100, multiplier=1)

        class FakeLedger:
            def __init__(self, conn):
                pass

            def last_ts(self):
                return NOW.timestamp()

        class FakeReader(ReaderHelpers):
            DEFAULT_PROJECT_GLOB = "*"
            Ledger = FakeLedger

            @staticmethod
            def open_ro(path):
                conn = sqlite3.connect(":memory:")
                conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
                conn.execute("INSERT INTO meta VALUES ('last_ingest', ?)", (str(NOW.timestamp()),))
                return conn

        payload = read_local_ledger.build_input(FakeReader, Path("unused"), NOW, self.db)
        snapshot = collect_gauges.build_snapshot(payload, NOW)

        copilot = next(dial for dial in snapshot["providers"] if dial["id"] == "copilot")
        self.assertEqual(copilot["used"], 1)
        self.assertEqual(copilot["unit"], "requests")
        self.assertEqual(copilot["state"], "uncalibrated")


if __name__ == "__main__":
    unittest.main()
