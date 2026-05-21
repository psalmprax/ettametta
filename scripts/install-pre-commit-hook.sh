#!/usr/bin/env bash
# =========================================================================
# Install the pre-commit hook for patch target validation
# =========================================================================
# Symlinks .githooks/pre-commit into .git/hooks/pre-commit so that
# the validation script runs automatically on every git commit.
#
# Usage:
#   bash scripts/install-pre-commit-hook.sh
# =========================================================================

set -o errexit
set -o nounset

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
HOOK_SOURCE="$REPO_ROOT/.githooks/pre-commit"
HOOK_TARGET="$REPO_ROOT/.git/hooks/pre-commit"

if [ ! -f "$HOOK_SOURCE" ]; then
    echo "❌  Hook source not found: $HOOK_SOURCE"
    exit 1
fi

if [ ! -d "$REPO_ROOT/.git/hooks" ]; then
    echo "❌  .git/hooks directory not found. Are you in the project root?"
    exit 1
fi

# Remove existing hook if present (plain file or stale symlink)
if [ -e "$HOOK_TARGET" ] || [ -L "$HOOK_TARGET" ]; then
    rm -f "$HOOK_TARGET"
    echo "🗑️  Removed existing pre-commit hook."
fi

ln -s "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_SOURCE"

echo "✅  Pre-commit hook installed: $HOOK_TARGET → $HOOK_SOURCE"
echo "   The hook will run 'validate_patch_targets.py --staged' on every commit."
echo "   To bypass: git commit --no-verify"
