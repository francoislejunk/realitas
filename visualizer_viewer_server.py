import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    if load_dotenv is not None:
        load_dotenv()
except Exception:
    pass


class _ViewerHandler(BaseHTTPRequestHandler):
    server_version = "RealitasNeoViewer/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path or "/"

        if path == "/" or path == "/index.html":
            self._serve_index()
            return

        if path == "/latest.png":
            self._serve_latest_png()
            return

        if path == "/latest.mp4":
            self._serve_latest_mp4()
            return

        if path == "/meta":
            self._serve_meta()
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return

    def _serve_index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        html = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Realitas Neo - Latest Image</title>
  <style>
    body { background: #0b0e14; color: #e6e6e6; font-family: ui-sans-serif, system-ui, -apple-system; margin: 0; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 16px; }
    h1 { font-size: 16px; margin: 0 0 8px 0; opacity: 0.9; }
    .hint { font-size: 12px; opacity: 0.7; margin-bottom: 12px; }
    img { width: 100%; background: #000; border-radius: 8px; display: block; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Latest image</h1>
    <div class=\"hint\">Auto-refreshes when latest.png changes</div>
    <img id=\"im\" alt=\"latest\" />
  </div>
  <script>
    const im = document.getElementById('im');
    let lastMtime = null;

    async function refresh() {
      try {
        const r = await fetch('/meta', { cache: 'no-store' });
        if (!r.ok) return;
        const meta = await r.json();
        if (!meta || !meta.mtime) return;
        if (lastMtime === null || meta.mtime !== lastMtime) {
          lastMtime = meta.mtime;
          im.src = '/latest.png?t=' + encodeURIComponent(String(meta.mtime));
        }
      } catch (e) {}
    }

    refresh();
    setInterval(refresh, 1500);
  </script>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def _serve_latest_png(self):
        image_path = getattr(self.server, "image_path", None)
        if not image_path or not os.path.exists(image_path):
            self.send_response(404)
            self.end_headers()
            return

        try:
            size = os.path.getsize(image_path)
        except Exception:
            size = None

        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "no-store")
        if size is not None:
            self.send_header("Content-Length", str(size))
        self.end_headers()

        with open(image_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 256)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _serve_latest_mp4(self):
        video_path = getattr(self.server, "video_path", None)
        if not video_path or not os.path.exists(video_path):
            self.send_response(404)
            self.end_headers()
            return

        try:
            size = os.path.getsize(video_path)
        except Exception:
            size = None

        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Cache-Control", "no-store")
        if size is not None:
            self.send_header("Content-Length", str(size))
        self.end_headers()

        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 256)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _serve_meta(self):
        image_path = getattr(self.server, "image_path", None)
        video_path = getattr(self.server, "video_path", None)
        mtime = 0
        path = image_path or video_path
        if path and os.path.exists(path):
            try:
                mtime = int(os.path.getmtime(path))
            except Exception:
                mtime = 0

        body = ("{\"mtime\":" + str(mtime) + "}").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_viewer_server(*, host: str = "127.0.0.1", port: int = 8765, video_path: str = None, image_path: str = None, open_browser: bool = True) -> ThreadingHTTPServer:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not image_path:
        image_path = os.path.join(base_dir, "simulation_data", "visualizer", "latest.png")
    if not video_path:
        video_path = os.path.join(base_dir, "simulation_data", "visualizer", "latest.mp4")

    httpd = ThreadingHTTPServer((host, int(port)), _ViewerHandler)
    httpd.video_path = video_path
    httpd.image_path = image_path

    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    if open_browser:
        try:
            webbrowser.open(f"http://{host}:{int(port)}/")
        except Exception:
            pass

    return httpd


if __name__ == "__main__":
    host = os.getenv("VIS_VIEWER_HOST") or "127.0.0.1"
    try:
        port = int(os.getenv("VIS_VIEWER_PORT") or "8765")
    except Exception:
        port = 8765

    base_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(base_dir, "simulation_data", "visualizer", "latest.mp4")
    image_path = os.path.join(base_dir, "simulation_data", "visualizer", "latest.png")
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    start_viewer_server(host=host, port=port, video_path=video_path, image_path=image_path, open_browser=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
