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

    def make_remote_writer(self):
        writer = Path(self.temporary.name) / "remote-writer"
        self.git("clone", self.remote, writer, cwd=self.temporary.name)
        return writer

    def commit_remote_gauge_change(self, writer, generated_at):
        snapshot_path = writer / "data" / "gauges.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["generated_at"] = generated_at
        snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        self.git("add", "data/gauges.json", cwd=writer)
        self.git("commit", "-m", "manual gauge refresh", cwd=writer)
        self.git("push", "origin", "main", cwd=writer)

    def assert_refresh_checkout_clean(self):
        self.assertEqual(self.git("branch", "--show-current", cwd=self.repo).stdout.strip(), "main")
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all", cwd=self.repo).stdout, "")
        self.assertFalse((self.repo / ".git" / "rebase-merge").exists())
        self.assertFalse((self.repo / ".git" / "rebase-apply").exists())

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

    def test_remote_gauge_change_is_fast_forwarded_before_collection(self):
        writer = self.make_remote_writer()
        self.commit_remote_gauge_change(writer, "2026-10-16T23:00:00Z")

        result = self.run_refresh()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assert_refresh_checkout_clean()
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.remote_commit())

        next_result = self.run_refresh()
        self.assertEqual(next_result.returncode, 0, next_result.stderr + next_result.stdout)
        self.assert_refresh_checkout_clean()

    def test_unpushed_local_commit_is_refused_without_changing_or_pushing_it(self):
        human_file = self.repo / "unpublished.txt"
        human_file.write_text("local work\n", encoding="utf-8")
        self.git("add", "unpublished.txt", cwd=self.repo)
        self.git("commit", "-m", "local human work", cwd=self.repo)
        human_commit = self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip()

        result = self.run_refresh()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result=failed:local-commits-not-pushed", (
            self.state / "ai-workflow" / "refresh_gauges.log"
        ).read_text())
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), human_commit)
        self.assertEqual(self.remote_commit(), self.initial_commit)
        self.assertEqual(human_file.read_text(encoding="utf-8"), "local work\n")
        self.assertEqual(self.git("status", "--porcelain", cwd=self.repo).stdout, "")
        self.assertEqual(
            (self.repo / "data" / "gauges.json").read_text(encoding="utf-8"),
            self.original_snapshot,
        )

    def test_rejected_push_aborts_conflicting_rebase_and_next_run_succeeds(self):
        writer = self.make_remote_writer()
        bin_dir = Path(self.temporary.name) / "bin"
        bin_dir.mkdir()
        wrapper = bin_dir / "git"
        marker = Path(self.temporary.name) / "remote-updated"
        reset_log = Path(self.temporary.name) / "reset-log"
        wrapper.write_text(
            """#!/bin/sh
if [ "$1" = "push" ] && [ ! -e "$MARKER" ]; then
    python3 - "$WRITER/data/gauges.json" "$REMOTE_GENERATED_AT" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
snapshot = json.loads(path.read_text(encoding="utf-8"))
snapshot["generated_at"] = sys.argv[2]
path.write_text(json.dumps(snapshot, indent=2) + "\\n", encoding="utf-8")
PY
    "$REAL_GIT" -C "$WRITER" add data/gauges.json
    "$REAL_GIT" -C "$WRITER" commit -m "manual gauge refresh"
    "$REAL_GIT" -C "$WRITER" push origin main
    touch "$MARKER"
fi
if [ "$1" = "reset" ]; then
    before=$("$REAL_GIT" rev-parse HEAD)
    for target do :; done
    printf '%s %s\\n' "$before" "$target" >> "$RESET_LOG"
fi
exec "$REAL_GIT" "$@"
""",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        result = self.run_refresh(
            PATH=f"{bin_dir}:{os.environ['PATH']}",
            REAL_GIT=shutil.which("git"),
            MARKER=str(marker),
            WRITER=str(writer),
            RESET_LOG=str(reset_log),
            REMOTE_GENERATED_AT="2026-10-16T22:00:00Z",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assert_refresh_checkout_clean()
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.initial_commit)
        reset_entries = reset_log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(reset_entries), 1)
        removed_commit, reset_target = reset_entries[0].split()
        self.assertEqual(reset_target, self.initial_commit)
        self.assertEqual(
            self.git("rev-list", "--count", f"{self.initial_commit}..{removed_commit}", cwd=self.repo)
            .stdout.strip(),
            "1",
        )
        self.assertEqual(
            self.git("rev-parse", f"{removed_commit}^", cwd=self.repo).stdout.strip(),
            self.initial_commit,
        )
        self.assertEqual(
            self.git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", removed_commit, cwd=self.repo
            ).stdout.splitlines(),
            ["data/gauges.json"],
        )
        self.assertEqual(
            self.git("show", "-s", "--format=%s", removed_commit, cwd=self.repo).stdout.strip(),
            "gauges: refresh data",
        )
        self.assertNotEqual(self.remote_commit(), self.initial_commit)

        next_result = self.run_refresh()
        self.assertEqual(next_result.returncode, 0, next_result.stderr + next_result.stdout)
        self.assert_refresh_checkout_clean()

    def test_failed_commit_restores_and_unstages_data_for_next_run(self):
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)

        result = self.run_refresh()
        self.assertNotEqual(result.returncode, 0)
        self.assert_refresh_checkout_clean()
        self.assertEqual(
            (self.repo / "data" / "gauges.json").read_text(encoding="utf-8"),
            self.original_snapshot,
        )
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.initial_commit)

        hook.unlink()
        next_result = self.run_refresh()
        self.assertEqual(next_result.returncode, 0, next_result.stderr + next_result.stdout)
        self.assert_refresh_checkout_clean()

    def test_gitleaks_finding_prevents_commit_and_unstages_data(self):
        bin_dir = Path(self.temporary.name) / "bin"
        bin_dir.mkdir()
        gitleaks = bin_dir / "gitleaks"
        gitleaks.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        gitleaks.chmod(0o755)

        result = self.run_refresh(PATH=f"{bin_dir}:{os.environ['PATH']}")
        self.assertNotEqual(result.returncode, 0)
        self.assert_refresh_checkout_clean()
        self.assertEqual(
            (self.repo / "data" / "gauges.json").read_text(encoding="utf-8"),
            self.original_snapshot,
        )
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.repo).stdout.strip(), self.initial_commit)
        self.assertEqual(self.remote_commit(), self.initial_commit)


if __name__ == "__main__":
    unittest.main()
