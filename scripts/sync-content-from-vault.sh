#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VAULT_PUBLIC_DIR="$(cd -- "/Users/skypawalker/Dropbox/Obsidian/public" && pwd)"
CONTENT_DIR="$PROJECT_DIR/content"

mkdir -p "$CONTENT_DIR"
rsync -a --delete \
  --exclude ".DS_Store" \
  --exclude ".obsidian" \
  --exclude ".git" \
  "$VAULT_PUBLIC_DIR/" "$CONTENT_DIR/"

echo "Synced $VAULT_PUBLIC_DIR to $CONTENT_DIR"
