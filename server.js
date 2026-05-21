const fs = require('fs');
const http = require('http');
const path = require('path');

const port = Number(process.env.PORT || 3000);
const version = process.env.REALITAS_VERSION || 'dev';
const worldStateFile = process.env.REALITAS_WORLD_STATE_FILE || path.join(process.cwd(), 'data', 'world-state.json');

const defaultWorldState = {
  world: {
    name: 'Realitas Dev Shard',
    status: 'online',
    promise: 'AI Reality Simulator',
  },
  actors: [],
  recent_events: [],
};

function withDefaults(rawState = {}, source) {
  const world = { ...defaultWorldState.world, ...(rawState.world || {}) };
  return {
    service: 'realitas',
    version,
    source,
    world,
    actors: Array.isArray(rawState.actors) ? rawState.actors : [],
    recent_events: Array.isArray(rawState.recent_events) ? rawState.recent_events : [],
    pillars: ['Immersive', 'Intuitive', 'Addictive'],
    runtime: {
      ingress: 'cloudflare-tunnel',
      hostname: 'dev.subrealiti.es',
      health: '/health',
    },
  };
}

function worldSnapshot() {
  try {
    const parsed = JSON.parse(fs.readFileSync(worldStateFile, 'utf8'));
    return withDefaults(parsed, { kind: 'file', path: worldStateFile });
  } catch (error) {
    return withDefaults(defaultWorldState, { kind: 'fallback', reason: error.code || 'parse_error' });
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderPage() {
  const snapshot = worldSnapshot();
  const worldName = escapeHtml(snapshot.world.name);
  const status = escapeHtml(snapshot.world.status);
  const location = escapeHtml(snapshot.world.location || 'awaiting vessel');
  const actorCount = snapshot.actors.length;
  const eventCount = snapshot.recent_events.length;
  const sourceLabel = snapshot.source.kind === 'file' ? 'persisted state' : 'fallback state';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Realitas</title>
  <style>
    :root { color-scheme: dark; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      min-height: 100vh;
      margin: 0;
      background: radial-gradient(circle at 50% 20%, #18223a 0, #08090d 55%, #020203 100%);
      color: #fff;
    }
    .container {
      width: min(980px, calc(100vw - 2rem));
      margin: 0 auto;
      padding: 10vh 0;
      text-align: center;
    }
    h1 { font-size: clamp(3rem, 8vw, 6rem); margin: 0 0 0.5rem; letter-spacing: -0.05em; }
    p { color: #a7adbd; font-size: 1.2rem; margin: 0.35rem 0; }
    .tag { color: #6e7890; font-size: 0.9rem; margin-top: 1.25rem; }
    .world-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-top: 2rem;
    }
    .card {
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 18px;
      background: rgba(8, 10, 16, 0.72);
      padding: 1rem;
      text-align: left;
      box-shadow: 0 18px 80px rgba(0, 0, 0, 0.28);
    }
    .label { color: #6e7890; font-size: 0.75rem; letter-spacing: 0.12em; text-transform: uppercase; }
    .value { color: #f4f7ff; font-size: 1rem; margin-top: 0.35rem; }
  </style>
</head>
<body>
  <main class="container">
    <h1>🌀 Realitas</h1>
    <p>${escapeHtml(snapshot.world.promise)}</p>
    <p class="tag">Pipeline online · ${escapeHtml(version)} · ${escapeHtml(sourceLabel)}</p>
    <section class="world-grid" aria-label="Realitas runtime state">
      <article class="card"><div class="label">World</div><div class="value">${worldName}</div></article>
      <article class="card"><div class="label">Status</div><div class="value">${status}</div></article>
      <article class="card"><div class="label">Location</div><div class="value">${location}</div></article>
      <article class="card"><div class="label">Actors</div><div class="value">${actorCount}</div></article>
      <article class="card"><div class="label">Recent Events</div><div class="value">${eventCount}</div></article>
      <article class="card"><div class="label">Pillars</div><div class="value">Immersive · Intuitive · Addictive</div></article>
    </section>
  </main>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
  if (req.url === '/health' || req.url === '/healthz') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify({ ok: true, service: 'realitas', version }));
    return;
  }

  if (req.url === '/api/world') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(worldSnapshot()));
    return;
  }

  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(renderPage());
});

server.listen(port, '0.0.0.0', () => {
  console.log(`Realitas running on :${port}`);
});
