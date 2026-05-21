const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

async function waitForHealth(baseUrl) {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) return;
    } catch (_) {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`server did not become healthy at ${baseUrl}`);
}

async function withServer(testFn, env = {}) {
  const port = 3200 + Math.floor(Math.random() * 1000);
  const baseUrl = `http://127.0.0.1:${port}`;
  const child = spawn(process.execPath, ['server.js'], {
    cwd: process.cwd(),
    env: { ...process.env, PORT: String(port), REALITAS_VERSION: 'test', ...env },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let stderr = '';
  child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
  try {
    await waitForHealth(baseUrl);
    await testFn(baseUrl);
  } finally {
    child.kill('SIGTERM');
    await once(child, 'exit').catch(() => {});
  }
  if (child.exitCode && child.exitCode !== 0 && child.signalCode !== 'SIGTERM') {
    throw new Error(`server exited unexpectedly ${child.exitCode}: ${stderr}`);
  }
}

async function testHealthContract() {
  await withServer(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/health`);
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.deepEqual(payload, { ok: true, service: 'realitas', version: 'test' });
  });
}

async function testWorldContractFallback() {
  await withServer(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/api/world`);
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.equal(payload.service, 'realitas');
    assert.equal(payload.version, 'test');
    assert.equal(payload.world.name, 'Realitas Dev Shard');
    assert.equal(payload.source.kind, 'fallback');
    assert.deepEqual(payload.pillars, ['Immersive', 'Intuitive', 'Addictive']);
    assert.equal(payload.runtime.ingress, 'cloudflare-tunnel');
    assert.equal(payload.runtime.hostname, 'dev.subrealiti.es');
  }, { REALITAS_WORLD_STATE_FILE: path.join(os.tmpdir(), 'missing-realitas-world-state.json') });
}

async function testWorldContractReadsPersistedState() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'realitas-world-'));
  const stateFile = path.join(dir, 'world-state.json');
  fs.writeFileSync(stateFile, JSON.stringify({
    world: {
      name: 'Nua Dawn Market',
      status: 'active-simulation',
      promise: 'NPCs keep moving when the vessel is absent',
      location: 'Harbor Market',
      world_time: { day: 3, hour: 7, minute: 45 },
    },
    actors: [
      { id: 'nua', name: 'Nua', role: 'vessel', state: 'listening' },
      { id: 'mara', name: 'Mara', role: 'merchant', state: 'negotiating' },
    ],
    recent_events: [
      { type: 'rumor', summary: 'A crane accident changed the morning routes.', importance: 7 },
    ],
  }), 'utf8');

  await withServer(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/api/world`);
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.equal(payload.service, 'realitas');
    assert.equal(payload.version, 'test');
    assert.equal(payload.source.kind, 'file');
    assert.equal(payload.source.path.endsWith('world-state.json'), true);
    assert.equal(payload.world.name, 'Nua Dawn Market');
    assert.equal(payload.world.status, 'active-simulation');
    assert.equal(payload.world.location, 'Harbor Market');
    assert.equal(payload.actors.length, 2);
    assert.equal(payload.recent_events[0].summary, 'A crane accident changed the morning routes.');
    assert.deepEqual(payload.pillars, ['Immersive', 'Intuitive', 'Addictive']);
  }, { REALITAS_WORLD_STATE_FILE: stateFile });
}

(async () => {
  await testHealthContract();
  await testWorldContractFallback();
  await testWorldContractReadsPersistedState();
  console.log('server contract ok');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
