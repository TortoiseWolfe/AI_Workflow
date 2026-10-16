import copy
import html.parser
import json
import re
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collect_gauges

FIXTURE_PATH = ROOT / "tests" / "fixtures" / "gauge-input.json"
SNAPSHOT_PATH = ROOT / "data" / "gauges.json"
PAGE_PATH = ROOT / "gauges.html"
NOW = datetime(2026, 10, 16, 15, 0, tzinfo=timezone.utc)

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
SECRET = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|"
    r"github_pat_[A-Za-z0-9_]{12,}|AIza[0-9A-Za-z_-]{20,}|"
    r"AKIA[0-9A-Z]{16}|Bearer\s+\S+)\b",
    re.I,
)
REPOSITORY_PATH = re.compile(r"(?<![:/\w])[A-Za-z0-9_-]{2,}/[A-Za-z0-9_-]{2,}(?![./\w])")
TASK_REFERENCE = re.compile(r"\b(?:TASK|ISSUE|TICKET)[-_ ]?#?[A-Z0-9][A-Z0-9_-]{3,}\b", re.I)
FORBIDDEN_FIELDS = {"repo", "repository", "task", "task_id", "task_name", "client", "client_name",
                    "email", "key", "api_key", "token", "session", "lane", "branch", "path"}


class ResourceParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.external_hosts = set()
        self.visible_text = []
        self.ignored_tags = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignored_tags += 1
        for name, value in attrs:
            if name not in {"href", "src"} or not value or not value.startswith(("http://", "https://")):
                continue
            host = value.split("/", 3)[2].split(":", 1)[0].lower()
            self.external_hosts.add(host)

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.ignored_tags:
            self.ignored_tags -= 1

    def handle_data(self, data):
        if not self.ignored_tags:
            self.visible_text.append(data)


def public_string_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from public_string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from public_string_values(item)
    elif isinstance(value, str):
        yield value


def reject_private_strings(text):
    for pattern in (EMAIL, SECRET, REPOSITORY_PATH, TASK_REFERENCE):
        if pattern.search(text):
            raise AssertionError(f"public content matches a private-identifier pattern: {pattern.pattern}")


def reject_private_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_FIELDS:
                raise AssertionError(f"private field name is not allowed: {key}")
            reject_private_fields(item)
    elif isinstance(value, list):
        for item in value:
            reject_private_fields(item)


class GaugePrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        cls.page = PAGE_PATH.read_text(encoding="utf-8")

    def dial(self, snapshot, dial_id):
        return next(item for item in snapshot["providers"] if item["id"] == dial_id)

    def test_published_file_contains_only_allowlisted_aggregate_fields(self):
        collect_gauges.validate_snapshot(self.snapshot)
        self.assertEqual(len(self.snapshot["providers"]), 15)
        reject_private_fields(self.snapshot)

    def test_schema_and_publisher_enforce_the_same_exact_fields(self):
        schema = json.loads((ROOT / "data" / "gauges.schema.json").read_text(encoding="utf-8"))
        dial_schema = schema["$defs"]["dial"]
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(dial_schema["additionalProperties"])
        self.assertEqual(
            set(dial_schema["properties"]),
            {
                "as_of", "id", "display_name", "kind", "window", "weight", "used",
                "limit", "unit", "percent", "state", "resets_at", "source",
                "context", "context_state",
            },
        )
        self.assertEqual(set(dial_schema["properties"]["context"]["properties"]), set(collect_gauges.CONTEXT_FIELDS))
        self.assertEqual(
            set(dial_schema["properties"]["id"]["enum"]),
            {dial["id"] for dial in self.snapshot["providers"]},
        )

    def test_public_page_and_data_have_no_identifier_or_secret_patterns(self):
        for value in public_string_values(self.snapshot):
            if value != "requests/hour":
                reject_private_strings(value)
        self.assertNotIn("application/json", self.page)
        parser = ResourceParser()
        parser.feed(self.page)
        reject_private_strings(" ".join(parser.visible_text))
        self.assertEqual(parser.external_hosts, set())  # SC-006: no third-party requests
        self.assertNotRegex(self.page, r"fetch\(\s*['\"]https?://")

    def test_page_has_responsive_light_dark_and_reduced_motion_support(self):
        self.assertIn("prefers-color-scheme: dark", self.page)
        self.assertIn("prefers-reduced-motion: reduce", self.page)
        self.assertIn("@media (max-width: 520px)", self.page)
        self.assertIn("aria-label=\"Provider and engine gauges\"", self.page)
        self.assertIn("Plain table view", self.page)

    def test_unknown_private_input_fields_are_rejected_before_output(self):
        for forbidden in ("repository", "task_name", "client_name", "api_key", "email"):
            with self.subTest(forbidden=forbidden):
                payload = copy.deepcopy(self.fixture)
                payload["calls"][0][forbidden] = "synthetic-private-value"
                with self.assertRaises(collect_gauges.InputError):
                    collect_gauges.build_snapshot(payload, NOW)

    def test_public_identifiers_and_labels_are_fixed_by_the_schema(self):
        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        snapshot["providers"][0]["id"] = "unlisted-provider"
        with self.assertRaises(collect_gauges.InputError):
            collect_gauges.validate_snapshot(snapshot)

        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        snapshot["providers"][0]["display_name"] = "Synthetic Client"
        with self.assertRaises(collect_gauges.InputError):
            collect_gauges.validate_snapshot(snapshot)

    def test_calibration_uses_full_window_and_tolerance(self):
        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        self.assertEqual(self.dial(snapshot, "gemini")["state"], "calibrated")
        self.assertEqual(self.dial(snapshot, "openrouter")["source"], "provider")
        self.assertEqual(self.dial(snapshot, "openrouter")["used"], 2)

        payload = copy.deepcopy(self.fixture)
        report = next(row for row in payload["provider_reports"] if row["provider_id"] == "gemini")
        report["used"] = 20
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        gemini = self.dial(snapshot, "gemini")
        self.assertEqual(gemini["state"], "uncalibrated")
        self.assertIsNone(gemini["percent"])

        report["window_complete"] = False
        report["used"] = 2
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        self.assertEqual(self.dial(snapshot, "gemini")["state"], "uncalibrated")

    def test_stale_boundary_is_twice_the_eight_hour_refresh_interval(self):
        payload = copy.deepcopy(self.fixture)
        old = "2026-10-15T12:00:00Z"
        for call in payload["calls"]:
            if call["provider_id"] == "gemini":
                call["timestamp"] = old
        report = next(row for row in payload["provider_reports"] if row["provider_id"] == "gemini")
        report["as_of"] = old
        report["used"] = 0
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        gemini = self.dial(snapshot, "gemini")
        self.assertEqual(gemini["state"], "stale")
        self.assertIsNone(gemini["percent"])
        self.assertIn("needle.stale", self.page)

    def test_a_quiet_provider_is_not_stale_but_a_silent_collector_is(self):
        payload = copy.deepcopy(self.fixture)
        payload["calls"] = [call for call in payload["calls"] if call["provider_id"] != "groq"]
        payload["calls"].append({"timestamp": "2026-10-14T09:00:00Z", "provider_id": "groq", "units": 1, "input_tokens": 10})
        payload["provider_reports"] = []
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        self.assertEqual(self.dial(snapshot, "groq")["state"], "uncalibrated")
        self.assertIsNone(self.dial(snapshot, "groq")["percent"])
        payload["ledger_as_of"] = "2026-10-15T12:00:00Z"
        for engine in payload["engines"]:
            if engine["as_of"]:
                engine["as_of"] = payload["ledger_as_of"]
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        self.assertEqual(self.dial(snapshot, "groq")["state"], "stale")
        self.assertEqual(self.dial(snapshot, "claude-opus")["state"], "stale")

    def test_an_engine_with_no_reader_stays_empty_and_context_is_never_called_calibrated(self):
        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        codex = self.dial(snapshot, "codex")
        self.assertIsNone(codex["as_of"])
        self.assertTrue(all(value is None for value in codex["context"].values()))
        for dial in snapshot["providers"]:
            self.assertNotIn("calibrated", dial["context_state"].values(), dial["id"])

    def test_activity_follows_the_last_ledger_row(self):
        self.assertEqual(collect_gauges.build_snapshot(self.fixture, NOW)["activity"], "working")
        payload = copy.deepcopy(self.fixture)
        payload["last_activity"] = "2026-10-16T09:00:00Z"
        self.assertEqual(collect_gauges.build_snapshot(payload, NOW)["activity"], "idle")

    def test_idle_unclaimed_and_codex_notice_are_explicit(self):
        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        self.assertEqual(self.dial(snapshot, "ollama")["state"], "idle")
        self.assertIsNone(self.dial(snapshot, "ollama")["percent"])
        self.assertEqual(self.dial(snapshot, "mistral")["state"], "unclaimed")
        self.assertIsNone(self.dial(snapshot, "mistral")["percent"])
        self.assertIn("No free usage until 31 Oct 2026", self.page)

    def test_compactions_are_suppressed_below_twenty_events(self):
        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        sonnet = self.dial(snapshot, "claude-sonnet")
        self.assertEqual(sonnet["context_state"]["compactions"], "uncalibrated")
        self.assertEqual(sonnet["context_state"]["input_tokens"], "not-applicable")
        self.assertIsNone(sonnet["context"]["compactions_total"])
        self.assertIn("too few", self.page)

    def test_compactions_publish_at_twenty_events(self):
        payload = copy.deepcopy(self.fixture)
        opus = next(row for row in payload["engines"] if row["id"] == "claude-opus")
        opus["compactions_total"] = 20
        opus["compactions_auto"] = 13
        opus["compactions_manual"] = 7
        snapshot = collect_gauges.build_snapshot(payload, NOW)
        context = self.dial(snapshot, "claude-opus")["context"]
        self.assertEqual(context["compactions_total"], 20)
        self.assertEqual(context["compactions_auto"], 13)
        self.assertEqual(context["compactions_manual"], 7)

    def test_atomic_output_is_written_from_in_repo_fixture(self):
        snapshot = collect_gauges.build_snapshot(self.fixture, NOW)
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            output = Path(directory) / "snapshot.json"
            collect_gauges.write_snapshot(snapshot, output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), snapshot)


if __name__ == "__main__":
    unittest.main()
