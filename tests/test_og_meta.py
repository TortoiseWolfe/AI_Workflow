"""Standing rule: every HTML page we publish carries Open Graph tags and a preview image."""
import html.parser
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://tortoisewolfe.github.io/AI_Workflow/"
REQUIRED_PROPERTIES = ("og:title", "og:description", "og:url", "og:image", "og:image:alt")


class MetaCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        a = dict(attrs)
        key = a.get("property") or a.get("name")
        if key and "content" in a:
            self.meta[key] = a["content"]


def published_pages():
    out = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [p for p in out.stdout.split() if not p.startswith("og/")]


class OgMetaTest(unittest.TestCase):
    def test_every_page_has_og_tags_and_a_real_preview_image(self):
        pages = published_pages()
        self.assertIn("gauges.html", pages)
        for page in pages:
            with self.subTest(page=page):
                parser = MetaCollector()
                parser.feed((ROOT / page).read_text())
                for key in REQUIRED_PROPERTIES:
                    self.assertTrue(parser.meta.get(key), f"{page} is missing {key}")
                self.assertEqual(parser.meta["og:url"], BASE + page)
                image = parser.meta["og:image"]
                self.assertTrue(image.startswith(BASE), f"{page}: og:image must be an absolute site URL")
                self.assertTrue((ROOT / image[len(BASE):]).is_file(), f"{page}: {image} is not in the repo")
                self.assertEqual(parser.meta.get("twitter:card"), "summary_large_image")
                self.assertEqual(parser.meta.get("twitter:image"), image)


if __name__ == "__main__":
    unittest.main()
