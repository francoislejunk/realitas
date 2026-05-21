#!/usr/bin/env bash
set -euo pipefail

# Realitas deploy helper.
# Default mode is read-only preflight. --apply mutates the VPS only when
# REALITAS_DEPLOY_CONFIRM=deploy-realitas is also set.
# Nginx replacement is separately gated by REALITAS_ENABLE_NGINX=1.

mode="preflight"
case "${1:---preflight}" in
  --apply) mode="apply" ;;
  --preflight) mode="preflight" ;;
  -h|--help)
    cat <<'USAGE'
Usage: scripts/deploy-realitas.sh [--preflight|--apply]

Environment:
  REALITAS_DEPLOY_HOST       default: realitas-dev
  REALITAS_DEPLOY_USER       default: root
  REALITAS_DEPLOY_SSH_KEY    default: /Users/frankmcalvarez/.ssh/hetzner_realitas
  REALITAS_REMOTE_DIR        default: /home/deploy/realitas
  REALITAS_SERVICE_NAME      default: realitas.service
  REALITAS_REPO_URL          default: origin URL
  REALITAS_BRANCH            default: current branch
  REALITAS_HEALTH_URL        default: http://127.0.0.1:3000/health
  REALITAS_START_CMD         default: /usr/bin/node server.js
  REALITAS_WORLD_STATE_FILE  default: data/world-state.json under the app dir
  REALITAS_CONTEXT_DB        default: simulation_data/context/context.db under the app dir
  REALITAS_DEPLOY_CONFIRM    must equal deploy-realitas for --apply
  REALITAS_ENABLE_NGINX      set to 1 to replace nginx routing after backup

--preflight is read-only: verifies SSH, remote tools, service state, and health.
--apply backs up the remote app, deploys the current commit, restarts systemd,
and probes local service health. Nginx is only changed when REALITAS_ENABLE_NGINX=1.
USAGE
    exit 0
    ;;
  *) echo "unknown argument: ${1:-}" >&2; exit 2 ;;
esac

repo_url_default="$(git remote get-url origin 2>/dev/null || true)"
branch_default="$(git branch --show-current 2>/dev/null || echo main)"

host="${REALITAS_DEPLOY_HOST:-realitas-dev}"
user="${REALITAS_DEPLOY_USER:-root}"
ssh_key="${REALITAS_DEPLOY_SSH_KEY:-/Users/frankmcalvarez/.ssh/hetzner_realitas}"
remote_dir="${REALITAS_REMOTE_DIR:-/home/deploy/realitas}"
service="${REALITAS_SERVICE_NAME:-realitas.service}"
repo_url="${REALITAS_REPO_URL:-$repo_url_default}"
branch="${REALITAS_BRANCH:-$branch_default}"
health_url="${REALITAS_HEALTH_URL:-http://127.0.0.1:3000/health}"
start_cmd="${REALITAS_START_CMD:-/usr/bin/node server.js}"
world_state_file="${REALITAS_WORLD_STATE_FILE:-$remote_dir/data/world-state.json}"
context_db="${REALITAS_CONTEXT_DB:-$remote_dir/simulation_data/context/context.db}"
enable_nginx="${REALITAS_ENABLE_NGINX:-0}"

if [[ -z "$repo_url" ]]; then
  echo "REALITAS_REPO_URL is required when origin is unavailable" >&2
  exit 2
fi
if [[ ! -r "$ssh_key" ]]; then
  echo "SSH key not readable: $ssh_key" >&2
  exit 2
fi

ssh_base=(ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i "$ssh_key" "${user}@${host}")

echo "== Realitas deploy $mode =="
echo "host=${user}@${host}"
echo "remote_dir=$remote_dir"
echo "service=$service"
echo "repo=$repo_url branch=$branch"
echo "health_url=$health_url"
echo "enable_nginx=$enable_nginx"
echo "world_state_file=$world_state_file"
echo "context_db=$context_db"

"${ssh_base[@]}" "REALITAS_REMOTE_DIR='$remote_dir' REALITAS_SERVICE_NAME='$service' REALITAS_HEALTH_URL='$health_url' bash -s" <<'REMOTE_PREFLIGHT'
set -euo pipefail
echo 'remote: connected'
command -v git >/dev/null && echo 'remote: git ok'
command -v systemctl >/dev/null && echo 'remote: systemctl ok'
command -v node >/dev/null && node --version | sed 's/^/remote: node /'
if [[ -d "$REALITAS_REMOTE_DIR" ]]; then
  echo 'remote: existing app dir present'
  ls -la "$REALITAS_REMOTE_DIR" | sed -n '1,40p'
else
  echo 'remote: app dir absent'
fi
systemctl is-active "$REALITAS_SERVICE_NAME" >/dev/null 2>&1 && echo 'remote: service active' || echo 'remote: service not active'
curl -fsS -m 5 "$REALITAS_HEALTH_URL" >/dev/null && echo 'remote: health ok' || echo 'remote: health not ok'
REMOTE_PREFLIGHT

if [[ "$mode" == "preflight" ]]; then
  echo "preflight complete; no remote mutation performed"
  exit 0
fi

if [[ "${REALITAS_DEPLOY_CONFIRM:-}" != "deploy-realitas" ]]; then
  echo "refusing --apply without REALITAS_DEPLOY_CONFIRM=deploy-realitas" >&2
  exit 3
fi

commit="$(git rev-parse HEAD)"
echo "applying commit $commit to ${user}@${host}:${remote_dir}"

"${ssh_base[@]}" \
  "REALITAS_REMOTE_DIR='$remote_dir' REALITAS_SERVICE_NAME='$service' REALITAS_REPO_URL='$repo_url' REALITAS_BRANCH='$branch' REALITAS_COMMIT='$commit' REALITAS_START_CMD='$start_cmd' REALITAS_WORLD_STATE_FILE='$world_state_file' REALITAS_CONTEXT_DB='$context_db' REALITAS_ENABLE_NGINX='$enable_nginx' bash -s" <<'REMOTE_APPLY'
set -euo pipefail
umask 022
backup_dir="${REALITAS_REMOTE_DIR}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
nginx_backup_dir="/root/realitas-nginx-backup.$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -e "$REALITAS_REMOTE_DIR" ]]; then
  echo "remote: backing up $REALITAS_REMOTE_DIR to $backup_dir"
  cp -a "$REALITAS_REMOTE_DIR" "$backup_dir"
fi
if [[ ! -d "$REALITAS_REMOTE_DIR/.git" ]]; then
  rm -rf "$REALITAS_REMOTE_DIR"
  git clone --branch "$REALITAS_BRANCH" "$REALITAS_REPO_URL" "$REALITAS_REMOTE_DIR"
fi
cd "$REALITAS_REMOTE_DIR"
git fetch origin "$REALITAS_BRANCH"
git checkout "$REALITAS_BRANCH"
git reset --hard "$REALITAS_COMMIT"

if [[ "${REALITAS_DEPLOY_INSTALL_PYTHON:-0}" == "1" && -f requirements.txt ]]; then
  if ! python3 -m venv .venv; then
    echo "remote: python venv unavailable; install python3-venv or leave REALITAS_DEPLOY_INSTALL_PYTHON=0 for the Node web shell" >&2
    exit 4
  fi
  . .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt pytest
  python -m pytest test_imports_quick.py
fi
if [[ -f package.json && -f package-lock.json ]]; then
  npm ci --omit=dev
elif [[ -f package.json ]]; then
  npm install --omit=dev
fi

if [[ -f "$REALITAS_CONTEXT_DB" && -f realitas_world_exporter.py ]]; then
  echo "remote: exporting world state from $REALITAS_CONTEXT_DB to $REALITAS_WORLD_STATE_FILE"
  python3 realitas_world_exporter.py \
    --db "$REALITAS_CONTEXT_DB" \
    --out "$REALITAS_WORLD_STATE_FILE" \
    --session "${REALITAS_CONTEXT_SESSION:-default}"
else
  echo "remote: world-state export skipped; context DB not found at $REALITAS_CONTEXT_DB"
fi

install -d -m 0755 /etc/realitas
cat > /etc/systemd/system/realitas.service <<SERVICE
[Unit]
Description=Realitas Web App
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=deploy
WorkingDirectory=$REALITAS_REMOTE_DIR
EnvironmentFile=-/etc/realitas/realitas.env
ExecStart=/bin/bash -lc 'exec $REALITAS_START_CMD'
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=$REALITAS_REMOTE_DIR

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
systemctl restart "$REALITAS_SERVICE_NAME"
systemctl --no-pager --full status "$REALITAS_SERVICE_NAME" | sed -n '1,80p'

if [[ "$REALITAS_ENABLE_NGINX" == "1" ]]; then
  echo "remote: backing up nginx site config to $nginx_backup_dir"
  install -d -m 0700 "$nginx_backup_dir"
  cp -a /etc/nginx/sites-available "$nginx_backup_dir/" 2>/dev/null || true
  cp -a /etc/nginx/sites-enabled "$nginx_backup_dir/" 2>/dev/null || true
  cat > /etc/nginx/sites-available/realitas <<'NGINX'
server {
    listen 80;
    server_name _;

    location /webhook/ {
        proxy_pass http://127.0.0.1:7842;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
  ln -sfn /etc/nginx/sites-available/realitas /etc/nginx/sites-enabled/realitas
  rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/gordon
  nginx -t
  systemctl reload nginx
else
  echo "remote: nginx unchanged; set REALITAS_ENABLE_NGINX=1 to replace routing after review"
fi

echo "remote: app rollback path: copy $backup_dir back to $REALITAS_REMOTE_DIR and systemctl restart $REALITAS_SERVICE_NAME"
if [[ "$REALITAS_ENABLE_NGINX" == "1" ]]; then
  echo "remote: nginx rollback path: restore sites-available/sites-enabled from $nginx_backup_dir, then nginx -t && systemctl reload nginx"
fi
REMOTE_APPLY

"${ssh_base[@]}" "curl -fsS -m 10 '$health_url' >/dev/null"
echo "deploy apply complete and health probe passed"
