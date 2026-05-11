#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
MESSAGE="${1:-Update content}"
BRANCH="$(git -C "$PROJECT_DIR" branch --show-current)"

cd "$PROJECT_DIR"

"$SCRIPT_DIR/sync-content-from-vault.sh"

if command -v mise >/dev/null 2>&1; then
  mise x node@22.16.0 -- npx quartz build
else
  npx quartz build
fi

git add -A

if git diff --cached --quiet; then
  echo "No changes to publish."
  exit 0
fi

git commit -m "$MESSAGE"
git push origin "$BRANCH"

echo "Pushed $BRANCH. GitHub Actions will deploy the site."
