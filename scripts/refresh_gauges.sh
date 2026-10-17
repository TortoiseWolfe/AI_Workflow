#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/ai-workflow"
LOG_FILE="$STATE_DIR/refresh_gauges.log"
LOCK_FILE="$STATE_DIR/refresh_gauges.lock"
RESULT="failed:unexpected"
GENERATED_AT=""
WORK_DIR=""
BACKUP_CREATED=0
COMMITTED=0
BASE_COMMIT=""
SCRIPT_COMMIT=""

mkdir -p -- "$STATE_DIR"

finish() {
    exit_code=$?
    trap - EXIT
    if (( exit_code != 0 && BACKUP_CREATED == 1 && COMMITTED == 0 )); then
        cp -- "$WORK_DIR/gauges.original.json" "$ROOT/data/gauges.json" || true
        git reset -q -- data/gauges.json || true
    fi
    if [[ -n "$WORK_DIR" ]]; then
        rm -f -- "$WORK_DIR/ledger-input.json" "$WORK_DIR/gauges.original.json"
        rmdir -- "$WORK_DIR"
    fi
    printf '%s result=%s generated_at=%s\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$RESULT" "${GENERATED_AT:-none}" >> "$LOG_FILE"
    exit "$exit_code"
}
trap finish EXIT

fail() {
    RESULT="failed:$1"
    printf 'refresh_gauges: %s\n' "$1" >&2
    exit 1
}

run_step() {
    label=$1
    shift
    if ! timeout --foreground 300 "$@"; then
        fail "$label"
    fi
}

reset_own_commit_to_base() {
    local head parent commits status

    if ! head="$(git rev-parse HEAD)" ||
        ! parent="$(git rev-parse HEAD^)" ||
        ! commits="$(git rev-list --count "$BASE_COMMIT..HEAD")" ||
        ! status="$(git status --porcelain --untracked-files=all)"; then
        return 1
    fi
    if [[ "$head" != "$SCRIPT_COMMIT" ||
        "$parent" != "$BASE_COMMIT" ||
        "$commits" != "1" ||
        -n "$status" ]]; then
        return 1
    fi
    git reset --hard -q "$BASE_COMMIT"
}

cd -- "$ROOT"
exec 9>"$LOCK_FILE"
if ! timeout --foreground 5 flock -n 9; then
    fail "already-running"
fi

if ! git_root="$(timeout --foreground 30 git rev-parse --show-toplevel)"; then
    fail "not-a-git-checkout"
fi
if [[ "$git_root" != "$ROOT" ]]; then
    fail "unexpected-git-root"
fi
if ! branch="$(timeout --foreground 30 git branch --show-current)"; then
    fail "branch-check-failed"
fi
if [[ "$branch" != "main" ]]; then
    fail "not-on-main"
fi
if ! status="$(timeout --foreground 30 git status --porcelain --untracked-files=all)"; then
    fail "worktree-check-failed"
fi
if [[ -n "$status" ]]; then
    fail "worktree-not-clean"
fi

run_step "pre-collection-pull-failed" git pull --ff-only origin main

if ! head_after_pull="$(timeout --foreground 30 git rev-parse HEAD)" ||
    ! origin_main_after_pull="$(timeout --foreground 30 git rev-parse refs/remotes/origin/main)"; then
    fail "post-pull-base-check-failed"
fi
if [[ "$head_after_pull" != "$origin_main_after_pull" ]]; then
    fail "local-commits-not-pushed"
fi
BASE_COMMIT="$head_after_pull"

WORK_DIR="$(mktemp -d "$STATE_DIR/.refresh-gauges.XXXXXX")"
chmod 700 "$WORK_DIR"
cp -- "$ROOT/data/gauges.json" "$WORK_DIR/gauges.original.json"
BACKUP_CREATED=1

run_step "ledger-reader-failed" python3 "$ROOT/scripts/read_local_ledger.py" \
    --output "$WORK_DIR/ledger-input.json"
run_step "gauge-collector-failed" python3 "$ROOT/scripts/collect_gauges.py" \
    --input "$WORK_DIR/ledger-input.json" \
    --output "$ROOT/data/gauges.json"

if ! timeout --foreground 120 python3 - "$ROOT" "$ROOT/data/gauges.json" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
snapshot_path = Path(sys.argv[2])
sys.path.insert(0, str(root / "scripts"))
from gauge_schema import validate_snapshot

with snapshot_path.open(encoding="utf-8") as snapshot_file:
    validate_snapshot(json.load(snapshot_file))
PY
then
    fail "schema-validation-failed"
fi

if ! GENERATED_AT="$(timeout --foreground 30 python3 - "$ROOT/data/gauges.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as snapshot_file:
    print(json.load(snapshot_file)["generated_at"])
PY
)"; then
    fail "generated-data-unreadable"
fi

run_step "privacy-tests-failed" python3 -m unittest discover \
    -s "$ROOT/tests" -p test_gauges_privacy.py

if timeout --foreground 30 git diff --quiet -- data/gauges.json; then
    RESULT="unchanged"
    exit 0
else
    diff_status=$?
fi
if [[ "$diff_status" -ne 1 ]]; then
    fail "diff-check-failed"
fi

if ! status="$(timeout --foreground 30 git status --porcelain --untracked-files=all)"; then
    fail "pre-commit-worktree-check-failed"
fi
if [[ "$status" != " M data/gauges.json" ]]; then
    fail "unexpected-worktree-changes"
fi

run_step "stage-failed" git add -- data/gauges.json
if ! staged_files="$(timeout --foreground 30 git diff --cached --name-only)"; then
    fail "staged-file-check-failed"
fi
if [[ "$staged_files" != "data/gauges.json" ]]; then
    fail "unexpected-staged-files"
fi
if command -v gitleaks >/dev/null 2>&1; then
    run_step "gitleaks-failed" gitleaks protect --staged --no-banner --redact
else
    printf '%s gitleaks=skipped:not-installed\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$LOG_FILE"
fi

run_step "commit-failed" git commit -m "gauges: refresh data"
COMMITTED=1
SCRIPT_COMMIT="$(timeout --foreground 30 git rev-parse HEAD)" ||
    fail "script-commit-check-failed"

if ! timeout --foreground 300 git push origin main; then
    if ! timeout --foreground 300 git pull --rebase origin main; then
        timeout --foreground 30 git rebase --abort || true
        rebase_merge="$(git rev-parse --git-path rebase-merge)"
        rebase_apply="$(git rev-parse --git-path rebase-apply)"
        if [[ -d "$rebase_merge" || -d "$rebase_apply" ]]; then
            fail "rebase-abort-failed"
        fi
        if ! reset_own_commit_to_base; then
            fail "pull-rebase-failed"
        fi
        fail "pull-rebase-failed"
    fi

    SCRIPT_COMMIT="$(timeout --foreground 30 git rev-parse HEAD)" ||
        fail "rebased-commit-check-failed"
    if ! timeout --foreground 300 git push origin main; then
        reset_own_commit_to_base || true
        fail "push-failed"
    fi
fi

RESULT="refreshed"
exit 0
