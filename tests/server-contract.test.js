const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { once } = require('node:events');

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

async function withServer(testFn) {
  const port = 3200 + Math.floor(Math.random() * 1000);
  const baseUrl = `http://127.0.0.1:${port}`;
  const child = spawn(process.execPath, ['server.js'], {
    cwd: process.cwd(),
    env: { ...process.env, PORT: String(port), REALITAS_VERSION: 'test' },
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

async function testWorldContract() {
  await withServer(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/api/world`);
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.equal(payload.service, 'realitas');
    assert.equal(payload.version, 'test');
    assert.equal(payload.world.name, 'Realitas Dev Shard');
    assert.deepEqual(payload.pillars, ['Immersive', 'Intuitive', 'Addictive']);
    assert.equal(payload.runtime.ingress, 'cloudflare-tunnel');
    assert.equal(payload.runtime.hostname, 'dev.subrealiti.es');
  });
}

(async () => {
  await testHealthContract();
  await testWorldContract();
  console.log('server contract ok');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
