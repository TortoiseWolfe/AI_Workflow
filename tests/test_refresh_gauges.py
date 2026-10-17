import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFRESHED_AT = "2026-10-17T00:00:00Z"


class RefreshGaugesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.repo = base / "checkout"
        self.remote = base / "remote.git"
        self.home = base / "home"
        self.state = base / "state"
        self.repo.mkdir()
        self.home.mkdir()
        (self.repo / "scripts").mkdir()
        (self.repo / "tests" / "fixtures").mkdir(parents=True)
        (self.repo / "data").mkdir()

        self.copy_file("scripts/refresh_gauges.sh")
        self.copy_file("scripts/gauge_schema.py")
        self.copy_file("scripts/collect_gauges.py", "scripts/collect_gauges_impl.py")
        self.copy_file("tests/test_gauges_privacy.py")
        self.copy_file("tests/fixtures/gauge-input.json")
        self.copy_file("gauges.html")
        self.copy_file("data/gauges.schema.json")
        self.copy_file(".gitignore")

        snapshot = json.loads((ROOT / "data" / "gauges.json").read_text(encoding="utf-8"))
        self.original_snapshot = json.dumps(snapshot, indent=2) + "\n"
        (self.repo / "data" / "gauges.json").write_text(self.original_snapshot, encoding="utf-8")

        self.write_stub_collectors()
        self.git("init", "--initial-branch=main", cwd=self.repo)
        self.git("init", "--bare", "--initial-branch=main", self.remote, cwd=base)
        self.git("remote", "add", "origin", str(self.remote), cwd=self.repo)
        self.git("add", "--all", cwd=self.repo)
        self.git("commit", "-m", "test fixture", cwd=self.repo)
        self.git("push", "--set-upstream", "origin", "main", cwd=self.repo)
        self.initial_commit = self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip()

    def tearDown(self):
        self.temporary.cleanup()

    def copy_file(self, relative_path, destination=None):
        source = ROOT / relative_path
        target = self.repo / (destination or relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if target.suffix == ".sh":
            target.chmod(0o755)

    def git(self, *args, cwd, check=True):
        return subprocess.run(
            ["git", *map(str, args)],
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "GIT_CONFIG_COUNT": "2",
                "GIT_CONFIG_KEY_0": "user.name",
                "GIT_CONFIG_VALUE_0": "automation",
                "GIT_CONFIG_KEY_1": "user.email",
                "GIT_CONFIG_VALUE_1": "automation",
            },
        )

    def write_stub_collectors(self):
        reader = """#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()
Path(args.output).write_text(json.dumps({}) + chr(10), encoding="utf-8")
"""
        collector = f"""#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from collect_gauges_impl import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.environ.get("GAUGES_STUB_INVALID") == "1":
        Path(args.output).write_text('{{"invalid": true}}' + chr(10), encoding="utf-8")
    else:
        snapshot_path = Path(__file__).resolve().parents[1] / "data" / "gauges.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["generated_at"] = os.environ.get("GAUGES_STUB_GENERATED_AT", "{REFRESHED_AT}")
        Path(args.output).write_text(json.dumps(snapshot, indent=2) + chr(10), encoding="utf-8")
"""
        (self.repo / "scripts" / "read_local_ledger.py").write_text(reader, encoding="utf-8")
        (self.repo / "scripts" / "collect_gauges.py").write_text(collector, encoding="utf-8")

    def run_refresh(self, **extra_env):
        env = {
            **os.environ,
            "HOME": str(self.home),
            "XDG_STATE_HOME": str(self.state),
            "GIT_AUTHOR_NAME": "automation",
            "GIT_AUTHOR_EMAIL": "automation",
            "GIT_COMMITTER_NAME": "automation",
            "GIT_COMMITTER_EMAIL": "automation",
            **extra_env,
        }
        return subprocess.run(
            ["bash", str(self.repo / "scripts" / "refresh_gauges.sh")],
            cwd=self.temporary.name,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def remote_commit(self):
        return self.git("--git-dir", self.remote, "rev-parse", "main", cwd=self.remote).stdout.strip()

    def test_changed_snapshot_is_validated_committed_and_pushed_alone(self):
        result = self.run_refresh()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn(
            f"generated_at={REFRESHED_AT}",
            (self.state / "ai-workflow" / "refresh_gauges.log").read_text(),
        )
        remote_commit = self.remote_commit()
        self.assertNotEqual(remote_commit, self.initial_commit)
        changed = self.git(
            "--git-dir", self.remote, "diff-tree", "--no-commit-id", "--name-only",
            "-r", remote_commit, cwd=self.remote,
        ).stdout.splitlines()
        self.assertEqual(changed, ["data/gauges.json"])
        self.assertEqual(self.git("status", "--porcelain", cwd=self.repo).stdout, "")

    def test_identical_snapshot_is_not_committed_or_pushed(self):
        snapshot = json.loads(self.original_snapshot)
        snapshot["generated_at"] = REFRESHED_AT
        (self.repo / "data" / "gauges.json").write_text(
            json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
        )
        self.git("add", "data/gauges.json", cwd=self.repo)
        self.git("commit", "-m", "seed identical snapshot", cwd=self.repo)
        self.git("push", "origin", "main", cwd=self.repo)
        before = self.remote_commit()

        result = self.run_refresh()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.remote_commit(), before)
        self.assertEqual(self.git("status", "--porcelain", cwd=self.repo).stdout, "")
        self.assertIn("result=unchanged", (self.state / "ai-workflow" / "refresh_gauges.log").read_text())

    def test_other_branch_is_refused(self):
        self.git("switch", "-c", "topic", cwd=self.repo)
        result = self.run_refresh()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_commit(), self.initial_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.initial_commit)
        self.assertIn("result=failed:not-on-main", (self.state / "ai-workflow" / "refresh_gauges.log").read_text())

    def test_other_dirty_file_is_refused(self):
        (self.repo / "unrelated.txt").write_text("work in progress\n", encoding="utf-8")
        result = self.run_refresh()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_commit(), self.initial_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.initial_commit)
        self.assertTrue((self.repo / "unrelated.txt").exists())

    def test_invalid_schema_is_not_committed_and_original_data_is_restored(self):
        result = self.run_refresh(GAUGES_STUB_INVALID="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_commit(), self.initial_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.initial_commit)
        self.assertEqual((self.repo / "data" / "gauges.json").read_text(encoding="utf-8"), self.original_snapshot)
        self.assertIn(
            "result=failed:schema-validation-failed",
            (self.state / "ai-workflow" / "refresh_gauges.log").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
