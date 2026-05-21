# Realitas deployment pipeline

## Current recovered state

- GitHub repo: `francoislejunk/realitas`, default branch `main`.
- CI gate: `.github/workflows/smoke.yml` runs `scripts/smoke-test.sh`.
- VPS: `realitas-dev`, public `178.104.92.122`, Tailscale `100.90.114.118`.
- SSH key: `/Users/frankmcalvarez/.ssh/hetzner_realitas`; Bitwarden has the deploy/infra credential metadata, but no secret values belong in this repo.
- Existing service: `realitas.service` runs as `deploy` from `/home/deploy/realitas` on port `3000`.
- Existing public nginx/Gordon routing must not be clobbered casually. Realitas public routing is separately gated.
- Cloudflared is token-managed on the VPS; local ingress config is not present, so exact public hostname remains a gate.

## Deployment shape

1. PRs must pass Smoke CI.
2. `main` is the deploy source for `/home/deploy/realitas`.
3. The current deployable web shell is `server.js` with `/health` and `/healthz`.
4. `.github/workflows/deploy.yml` is manual-only (`workflow_dispatch`) and requires the `confirm` input to equal `deploy-realitas`; merging this PR does not auto-mutate the VPS.
5. `scripts/deploy-realitas.sh --preflight` is read-only and verifies SSH, remote tools, service state, and local health.
6. `scripts/deploy-realitas.sh --apply` requires `REALITAS_DEPLOY_CONFIRM=deploy-realitas`, backs up the existing app directory, resets the VPS checkout to the deploying commit, restarts `realitas.service`, and probes local service health.
7. Nginx replacement requires a separate `REALITAS_ENABLE_NGINX=1` gate. When enabled, the helper backs up `/etc/nginx/sites-available` and `/etc/nginx/sites-enabled` before replacing routing.
8. GitHub Actions deploy requires repository secret `REALITAS_DEPLOY_SSH_KEY` and should only be run after the GitHub secret, SSH path, runtime target, and public hostname/routing decision are verified.

## Manual local preflight

```bash
scripts/deploy-realitas.sh --preflight
```

## Manual local deploy, service only

```bash
REALITAS_DEPLOY_CONFIRM=deploy-realitas scripts/deploy-realitas.sh --apply
```

## Manual local deploy, service plus nginx replacement

Only use after reviewing Gordon/default nginx impact and confirming this VPS should route port 80 `/` to Realitas:

```bash
REALITAS_DEPLOY_CONFIRM=deploy-realitas REALITAS_ENABLE_NGINX=1 scripts/deploy-realitas.sh --apply
```

## Health probes

```bash
scripts/health-probe.sh http://127.0.0.1:3000/health
scripts/health-probe.sh http://178.104.92.122/health
scripts/public-smoke-test.sh https://dev.subrealiti.es
```

## Rollback

The deploy helper prints the exact backup paths.

App rollback shape on the VPS:

```bash
systemctl stop realitas.service
rm -rf /home/deploy/realitas
cp -a /home/deploy/realitas.backup.<timestamp> /home/deploy/realitas
systemctl restart realitas.service
```

Nginx rollback shape when `REALITAS_ENABLE_NGINX=1` was used:

```bash
rm -rf /etc/nginx/sites-available /etc/nginx/sites-enabled
cp -a /root/realitas-nginx-backup.<timestamp>/sites-available /etc/nginx/sites-available
cp -a /root/realitas-nginx-backup.<timestamp>/sites-enabled /etc/nginx/sites-enabled
nginx -t && systemctl reload nginx
```

If only the app deploy was used, nginx is unchanged and only the app rollback is needed.

## Remaining gates before first live deploy

- Confirm `REALITAS_DEPLOY_SSH_KEY` exists as a GitHub Actions secret and matches the VPS deploy key.
- Confirm whether first deploy should run from local CLI or GitHub Actions.
- Confirm Realitas public hostname / Cloudflare Tunnel route, or decide to expose only through the VPS public IP first.
- Confirm nginx replacement timing because current Gordon/default routing is live state.
