#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/health-probe.sh [URL]

Default URL: ${REALITAS_HEALTH_URL:-http://127.0.0.1:3000/}
Performs a read-only HTTP probe and fails unless the endpoint returns HTTP 2xx/3xx.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

url="${1:-${REALITAS_HEALTH_URL:-http://127.0.0.1:3000/}}"
timeout="${REALITAS_HEALTH_TIMEOUT:-10}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 127
fi

status_file="$(mktemp)"
body_file="$(mktemp)"
trap 'rm -f "$status_file" "$body_file"' EXIT

http_code="$({ curl -fsS -L --max-time "$timeout" -o "$body_file" -w '%{http_code}' "$url" || true; } | tee "$status_file")"
http_code="$(cat "$status_file")"

if [[ ! "$http_code" =~ ^[0-9]{3}$ ]]; then
  echo "health probe failed: no HTTP status from $url" >&2
  exit 1
fi

if [[ "$http_code" -lt 200 || "$http_code" -ge 400 ]]; then
  echo "health probe failed: $url returned HTTP $http_code" >&2
  sed -n '1,20p' "$body_file" >&2 || true
  exit 1
fi

bytes="$(wc -c < "$body_file" | tr -d ' ')"
echo "health probe ok: $url returned HTTP $http_code (${bytes} bytes)"
