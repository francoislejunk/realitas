#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-${REALITAS_PUBLIC_BASE_URL:-https://dev.subrealiti.es}}"
base_url="${base_url%/}"

echo "public smoke: ${base_url}"

health_json="$(curl -fsS -L --max-time "${REALITAS_HEALTH_TIMEOUT:-10}" "${base_url}/health")"
REALITAS_HEALTH_JSON="$health_json" python3 - <<'PY'
import json, os
payload = json.loads(os.environ['REALITAS_HEALTH_JSON'])
assert payload.get('ok') is True, payload
assert payload.get('service') == 'realitas', payload
print('health json ok')
PY

page="$(curl -fsS -L --max-time "${REALITAS_HEALTH_TIMEOUT:-10}" "$base_url/")"
printf '%s\n' "$page" | grep -q 'Realitas'
printf '%s\n' "$page" | grep -q 'Pipeline online'
echo "page content ok"
