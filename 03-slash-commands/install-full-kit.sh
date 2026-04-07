#!/usr/bin/env bash
# install-full-kit.sh
#
# Copies the 35 advanced commands (orchestration, governance, wireframe, knowledge curation)
# from ~/repos/Claude_Commandz/global/.claude/commands/ into your global ~/.claude/commands/.
#
# These commands are NOT in the 30-command starter kit because they need additional
# infrastructure (tmux assembly line, RFC council, wireframe validator script, etc.).
# Install them when you're ready for Chapter 05.
#
# Run from anywhere:
#   bash ~/repos/AI_Workflow/03-slash-commands/install-full-kit.sh
#
# Idempotent — safe to re-run. Skips files that already exist unless --force.

set -euo pipefail

CLAUDE_COMMANDZ="${CLAUDE_COMMANDZ:-$HOME/repos/Claude_Commandz}"
SRC="${CLAUDE_COMMANDZ}/global/.claude/commands"
DST="$HOME/.claude/commands"
FORCE="${FORCE:-0}"

if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: source directory not found: $SRC" >&2
  echo "Clone Claude_Commandz first:" >&2
  echo "  git clone https://github.com/TurtleWolfe/Claude_Commandz.git ~/repos/Claude_Commandz" >&2
  echo "Or set CLAUDE_COMMANDZ env var to point at your clone." >&2
  exit 1
fi

mkdir -p "$DST"

# The 35 advanced commands, grouped by family
ORCHESTRATION=(
  dispatch.md
  queue.md
  queue-check.md
  review-queue.md
  next.md
  log.md
  refresh-inventories.md
)

GOVERNANCE=(
  rfc.md
  rfc-vote.md
  vote-now.md
  council.md
  broadcast.md
  memo.md
)

WIREFRAME=(
  wireframe.md
  wireframe-plan.md
  wireframe-prep.md
  wireframe-focused.md
  wireframe-fix.md
  wireframe-review.md
  wireframe-inspect.md
  wireframe-screenshots.md
  wireframe-status.md
  hot-reload-viewer.md
  viewer-status.md
)

KNOWLEDGE=(
  clean-transcript.md
  extract-linkedin.md
  rpg_subsystem_scaffold.md
)

ALL_FILES=("${ORCHESTRATION[@]}" "${GOVERNANCE[@]}" "${WIREFRAME[@]}" "${KNOWLEDGE[@]}")

installed=0
skipped=0
missing=0

for f in "${ALL_FILES[@]}"; do
  if [[ ! -f "$SRC/$f" ]]; then
    echo "  MISSING upstream: $f"
    missing=$((missing + 1))
    continue
  fi

  if [[ -f "$DST/$f" && "$FORCE" != "1" ]]; then
    skipped=$((skipped + 1))
    continue
  fi

  cp "$SRC/$f" "$DST/$f"
  installed=$((installed + 1))
done

echo
echo "═══════════════════════════════════════════"
echo "Full-kit install complete"
echo "═══════════════════════════════════════════"
echo "  Installed:        $installed"
echo "  Already present:  $skipped (use --force to overwrite)"
echo "  Missing upstream: $missing"
echo
echo "Source: $SRC"
echo "Destination: $DST"
echo
echo "Note: most of these need additional infrastructure to be useful."
echo "See Chapter 05 of AI_Workflow:"
echo "  ~/repos/AI_Workflow/05-advanced-orchestration/"
echo "═══════════════════════════════════════════"
