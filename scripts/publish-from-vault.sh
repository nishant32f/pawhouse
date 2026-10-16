#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--digest" ]]; then
  exec python3 "$SCRIPT_DIR/publication.py" digest --request "${2:?Pass a private accepted request JSON}"
fi
case "${1:-}" in
  digest|status|resume|recover|delivery-begin|delivery-complete|delivery-resolve)
    exec python3 "$SCRIPT_DIR/publication.py" "$@"
    ;;
esac
exec python3 "$SCRIPT_DIR/publication.py" notes --message "${1:-Update content}"
