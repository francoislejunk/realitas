const http = require('http');

const port = Number(process.env.PORT || 3000);
const version = process.env.REALITAS_VERSION || 'dev';

const page = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Realitas</title>
  <style>
    :root { color-scheme: dark; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      background: radial-gradient(circle at 50% 20%, #18223a 0, #08090d 55%, #020203 100%);
      color: #fff;
    }
    .container { text-align: center; padding: 2rem; }
    h1 { font-size: clamp(3rem, 8vw, 6rem); margin: 0 0 0.5rem; letter-spacing: -0.05em; }
    p { color: #a7adbd; font-size: 1.2rem; margin: 0.35rem 0; }
    .tag { color: #6e7890; font-size: 0.9rem; margin-top: 1.25rem; }
  </style>
</head>
<body>
  <main class="container">
    <h1>🌀 Realitas</h1>
    <p>AI Reality Simulator</p>
    <p class="tag">Pipeline online · ${version}</p>
  </main>
</body>
</html>`;

const server = http.createServer((req, res) => {
  if (req.url === '/health' || req.url === '/healthz') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify({ ok: true, service: 'realitas', version }));
    return;
  }

  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(page);
});

server.listen(port, '0.0.0.0', () => {
  console.log(`Realitas running on :${port}`);
});
