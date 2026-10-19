import datetime as dt
import sys
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import read_groq_limits as groq

NOW = dt.datetime(2026, 10, 19, 1, 0, tzinfo=dt.timezone.utc)
SECRET = "fixture-credential-value"


def headers(**fields):
    message = Message()
    for name, value in fields.items():
        message[name.replace("_", "-")] = value
    return message


class FakeResponse:
    def __init__(self, response_headers):
        self.headers = response_headers

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class GroqReaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.key_file = Path(self.directory.name) / "key"
        self.key_file.write_text(SECRET + "\n")
        self.sent = []

    def tearDown(self):
        self.directory.cleanup()

    def opener(self, remaining_by_model):
        def open_url(request, timeout):
            self.sent.append(request)
            model = __import__("json").loads(request.data)["model"]
            return FakeResponse(headers(
                x_ratelimit_limit_requests="1000",
                x_ratelimit_remaining_requests=str(remaining_by_model[model]),
            ))
        return open_url

    def test_report_sums_both_models_and_logs_each_probe(self):
        logged = []
        report = groq.groq_report(
            NOW, self.key_file,
            self.opener({"openai/gpt-oss-120b": 990, "qwen/qwen3.8-27b": 995}),
            log=logged.append,
        )

        self.assertEqual(report["provider_id"], "groq")
        self.assertEqual(report["used"], 15)
        self.assertEqual(report["limit"], 2000)
        self.assertEqual(report["refill_seconds"], 86.4)
        self.assertEqual(report["source"], "provider")
        self.assertTrue(report["window_complete"])
        self.assertEqual(report["as_of"], "2026-10-19T01:00:00Z")
        self.assertIsNone(report["resets_at"])
        self.assertEqual(logged, ["groq", "groq_qwen"])
        self.assertEqual(len(self.sent), 2)

    def test_key_goes_only_in_the_authorization_header(self):
        report = groq.groq_report(
            NOW, self.key_file,
            self.opener({"openai/gpt-oss-120b": 1000, "qwen/qwen3.8-27b": 1000}),
        )

        self.assertNotIn(SECRET, repr(report))
        for request in self.sent:
            self.assertEqual(request.get_header("Authorization"), f"Bearer {SECRET}")
            self.assertNotIn(SECRET, request.full_url)
            self.assertNotIn(SECRET.encode(), request.data)

    def test_missing_key_file_gives_no_report(self):
        self.assertIsNone(groq.groq_report(NOW, self.key_file.with_name("absent")))

    def test_missing_headers_give_no_report(self):
        def open_url(request, timeout):
            return FakeResponse(headers(x_ratelimit_limit_requests="1000"))

        self.assertIsNone(groq.groq_report(NOW, self.key_file, open_url))

    def test_rate_limited_response_still_reports_the_budget(self):
        def open_url(request, timeout):
            raise urllib.error.HTTPError(
                request.full_url, 429, "Too Many Requests",
                headers(x_ratelimit_limit_requests="1000", x_ratelimit_remaining_requests="0"), None,
            )

        report = groq.groq_report(NOW, self.key_file, open_url)

        self.assertEqual(report["used"], 2000)

    def test_network_failure_gives_no_report_and_logs_nothing(self):
        logged = []

        def open_url(request, timeout):
            raise urllib.error.URLError("down")

        self.assertIsNone(groq.groq_report(NOW, self.key_file, open_url, log=logged.append))
        self.assertEqual(logged, [])

    def test_impossible_headers_are_rejected(self):
        def open_url(request, timeout):
            return FakeResponse(headers(
                x_ratelimit_limit_requests="1000", x_ratelimit_remaining_requests="1001",
            ))

        self.assertIsNone(groq.groq_report(NOW, self.key_file, open_url))


if __name__ == "__main__":
    unittest.main()
