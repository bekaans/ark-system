"""
Bexi UI köprüsü — hands_free.py'nin olaylarını tarayıcı arayüzüne yayınlar.

Tasarım kararları:
- SSE (Server-Sent Events), WebSocket DEĞİL: UI'dan geriye komut gelmiyor
  (komutlar zaten mikrofondan geliyor), tek yönlü yayın yeterli. SSE
  stdlib'le çalışır — yeni pip bağımlılığı SIFIR. iPhone Safari dahil her
  modern tarayıcı destekler.
- hands_free.py'ye etkisi: UI_ENABLED=False ise emit() no-op, sunucu hiç
  başlamaz — motor davranışı bit düzeyinde aynı kalır.
- Aynı sunucu voice/ui/ altındaki statik dosyaları da servis eder, yani
  tek port (8123): Mac'te http://localhost:8123, telefonda http://<mac-ip>:8123.

Olay şeması (her satır bir JSON):
  {"type": "state", "value": "sleeping|listening|thinking|speaking"}
  {"type": "user",  "text": "..."}          # Kaan'ın transkripti
  {"type": "bexi",  "text": "..."}          # seslendirilen cümle
  {"type": "tool",  "text": "bir dosya okuyorum"}
  {"type": "hello", "history": [...]}       # yeni bağlanan istemciye replay
"""

from __future__ import annotations

import json
import queue
import socket
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UI_DIR = Path(__file__).parent / "ui"
HISTORY_LIMIT = 200  # yeni bağlanan istemciye gönderilecek geçmiş olay sayısı

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}


class UiBridge:
    """Olayları tutan + SSE istemcilerine dağıtan merkez."""

    def __init__(self, port: int = 8123):
        self.port = port
        self._clients: list[queue.Queue] = []
        self._lock = threading.Lock()
        self._history: deque = deque(maxlen=HISTORY_LIMIT)
        self._server: ThreadingHTTPServer | None = None

    def emit(self, type_: str, **fields) -> None:
        event = {"type": type_, "ts": time.time(), **fields}
        with self._lock:
            self._history.append(event)
            clients = list(self._clients)
        for q in clients:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass  # yavaş istemci olayı kaçırır, motoru asla bloklamayız

    def _register(self) -> tuple[queue.Queue, list]:
        q: queue.Queue = queue.Queue(maxsize=500)
        with self._lock:
            self._clients.append(q)
            history = list(self._history)
        return q, history

    def _unregister(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._clients:
                self._clients.remove(q)

    def start(self) -> str:
        """Sunucuyu arka plan thread'inde başlatır, erişim URL'ini döndürür."""
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):  # terminali kirletme
                pass

            def do_GET(self):
                if self.path == "/events":
                    self._serve_sse()
                else:
                    self._serve_static()

            def _serve_sse(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                q, history = bridge._register()
                try:
                    hello = {"type": "hello", "history": history}
                    self.wfile.write(f"data: {json.dumps(hello, ensure_ascii=False)}\n\n".encode())
                    self.wfile.flush()
                    while True:
                        try:
                            event = q.get(timeout=15)
                            payload = json.dumps(event, ensure_ascii=False)
                            self.wfile.write(f"data: {payload}\n\n".encode())
                        except queue.Empty:
                            # keep-alive yorumu — telefon uykudan dönünce
                            # kopukluğu erken fark etmemizi de sağlar
                            self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    bridge._unregister(q)

            def _serve_static(self):
                rel = self.path.split("?")[0].lstrip("/") or "index.html"
                target = (UI_DIR / rel).resolve()
                # dizin dışına kaçışı engelle
                if not str(target).startswith(str(UI_DIR.resolve())) or not target.is_file():
                    self.send_response(404)
                    self.end_headers()
                    return
                body = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", _MIME.get(target.suffix, "application/octet-stream"))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self._server = ThreadingHTTPServer(("0.0.0.0", self.port), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

        lan_ip = _lan_ip()
        return f"http://localhost:{self.port}  (telefondan: http://{lan_ip}:{self.port})"


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "<mac-ip>"


# hands_free.py'nin kullandığı global tekil örnek. UI_ENABLED=False iken
# hiç start() çağrılmaz; emit() de bağlı istemci olmadığından no-op kalır.
bridge = UiBridge()
