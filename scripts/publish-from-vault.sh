#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
MESSAGE="${1:-Update content}"

cd "$PROJECT_DIR"

"$SCRIPT_DIR/sync-content-from-vault.sh"

if command -v mise >/dev/null 2>&1; then
  mise x node@22.16.0 -- npx quartz build
else
  npx quartz build
fi

if git diff --quiet -- content && git diff --cached --quiet -- content; then
  echo "No content changes to publish."
  exit 0
fi

git add -A content
git commit -m "$MESSAGE"
git push

echo "Pushed content update. GitHub Actions will deploy the site."
