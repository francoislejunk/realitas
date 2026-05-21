# Realitas deployment pipeline

## Current recovered state

- GitHub repo: `francoislejunk/realitas`, default branch `main`.
- CI gate: `.github/workflows/smoke.yml` runs `scripts/smoke-test.sh`.
- VPS: `realitas-dev`, public `178.104.92.122`, Tailscale `100.90.114.118`.
- SSH key: `/Users/frankmcalvarez/.ssh/hetzner_realitas`.
- Existing service: `realitas.service` runs as `deploy` from `/home/deploy/realitas` on port `3000`.
- Existing public nginx preserves Gordon `/webhook/` and needs Realitas routed through `/`.
- Cloudflared is token-managed on the VPS; local ingress config is not present.

## Deployment shape

1. PRs must pass Smoke CI.
2. `main` is deployed to `/home/deploy/realitas`.
3. The current deployable web shell is `server.js` with `/health`.
4. `scripts/deploy-realitas.sh --apply` backs up the existing app directory, resets the VPS checkout to the deploying commit, restarts `realitas.service`, configures nginx, and probes health.
5. GitHub Actions deploy uses the repository secret `REALITAS_DEPLOY_SSH_KEY` and the public VPS IP.

## Manual local preflight

```bash
scripts/deploy-realitas.sh --preflight
```

## Manual local deploy

```bash
REALITAS_DEPLOY_CONFIRM=deploy-realitas scripts/deploy-realitas.sh --apply
```

## Health probes

```bash
scripts/health-probe.sh http://127.0.0.1:3000/health
scripts/health-probe.sh http://178.104.92.122/health
```

## Rollback

The deploy helper prints the exact backup directory. Rollback shape on the VPS:

```bash
systemctl stop realitas.service
rm -rf /home/deploy/realitas
cp -a /home/deploy/realitas.backup.<timestamp> /home/deploy/realitas
systemctl restart realitas.service
nginx -t && systemctl reload nginx
```

If only nginx is bad, restore the previous site link/config and run `nginx -t && systemctl reload nginx`.
