from __future__ import annotations

import argparse
import html
import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from .demo import build_demo_index
from .semantic import SemanticRanker


LANDING_PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Overmind</title>
<style>body{font-family:Arial,sans-serif;margin:2rem;background:#0b1020;color:#e7ecff}a{color:#8bb2ff} .card{background:#131a33;border-radius:12px;padding:1rem;max-width:900px}</style>
</head><body>
<h1>🧠 Overmind Local</h1>
<div class="card">
  <p><a href="/search">Recherche sémantique (démo)</a></p>
  <p><a href="/browser">Navigateur web local (mini browser)</a></p>
</div>
</body></html>"""

SEARCH_PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Overmind - Search</title>
<style>
body { font-family: Arial, sans-serif; margin: 2rem; background: #0b1020; color: #e7ecff; }
.card { background: #131a33; border-radius: 12px; padding: 1rem 1.2rem; max-width: 900px; }
input { width: 70%; padding: .7rem; border-radius: 8px; border: 1px solid #2b386e; background:#0f1530; color:#fff; }
button { padding: .7rem 1rem; border-radius: 8px; border: none; background: #4f7cff; color:#fff; cursor:pointer; }
li { margin: .8rem 0; }
.score { color: #8bb2ff; }
a { color: #8bb2ff; }
</style>
</head><body>
<h1>Recherche sémantique (démo)</h1>
<p><a href="/">← Accueil</a> | <a href="/browser">Ouvrir le navigateur</a></p>
<div class="card">
  <p>Essaie une requête (ex: <code>meilleur langage pour jeu 2d rapide</code>)</p>
  <input id="q" placeholder="Pose ta question" />
  <button id="go">Chercher</button>
  <ul id="results"></ul>
</div>
<script>
async function search() {
  const q = document.getElementById('q').value.trim();
  const ul = document.getElementById('results');
  ul.innerHTML = '';
  if (!q) return;
  const res = await fetch('/api/search?q=' + encodeURIComponent(q));
  const data = await res.json();
  for (const item of data.results) {
    const li = document.createElement('li');
    li.innerHTML = '<strong>' + item.title + '</strong> '
      + '<span class="score">(score: ' + item.score + ')</span><br/>'
      + '<small>' + item.url + '</small>';
    ul.appendChild(li);
  }
}
document.getElementById('go').addEventListener('click', search);
document.getElementById('q').addEventListener('keydown', (e) => { if (e.key === 'Enter') search(); });
</script>
</body></html>"""

BROWSER_PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Overmind Browser</title>
<style>
body { font-family: Arial, sans-serif; margin: 0; background: #0b1020; color: #e7ecff; }
header { padding: .8rem; background:#131a33; display:flex; gap:.5rem; align-items:center; }
input { flex:1; padding: .65rem; border-radius: 8px; border: 1px solid #2b386e; background:#0f1530; color:#fff; }
button,a.btn { padding: .6rem .9rem; border-radius: 8px; border: none; background: #4f7cff; color:#fff; cursor:pointer; text-decoration:none; }
iframe { width: 100%; height: calc(100vh - 62px); border: none; background: white; }
</style>
</head><body>
<header>
  <a class="btn" href="/">Accueil</a>
  <input id="url" placeholder="https://example.com" />
  <button id="go">Aller</button>
</header>
<iframe id="frame" src="/view?url=https%3A%2F%2Fexample.com"></iframe>
<script>
function navigate() {
  const raw = document.getElementById('url').value.trim();
  if (!raw) return;
  const normalized = raw.startsWith('http://') || raw.startsWith('https://') ? raw : ('https://' + raw);
  document.getElementById('frame').src = '/view?url=' + encodeURIComponent(normalized);
}
document.getElementById('go').addEventListener('click', navigate);
document.getElementById('url').addEventListener('keydown', (e) => { if (e.key === 'Enter') navigate(); });
</script>
</body></html>"""


def build_results(query: str) -> list[dict[str, str | float]]:
    index = build_demo_index()
    ranker = SemanticRanker(index)
    results = ranker.search(query, top_k=5)
    return [{"title": r.title, "url": r.url, "score": round(r.score, 4)} for r in results]


def normalize_target_url(url: str) -> str:
    candidate = url.strip()
    if not candidate:
        return ""
    if not candidate.startswith(("http://", "https://")):
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return candidate


def fetch_remote_html(url: str, timeout: int = 8) -> tuple[str, str]:
    req = Request(url, headers={"User-Agent": "OvermindBrowser/0.1"})
    with urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            raise ValueError(f"Only text/html supported (got: {content_type})")
        body = response.read().decode("utf-8", errors="ignore")
        return body, content_type


def _rewrite_links(raw_html: str, base_url: str) -> str:
    def href_repl(match: re.Match[str]) -> str:
        prefix, link = match.group(1), match.group(2)
        absolute = urljoin(base_url, html.unescape(link))
        safe = quote(absolute, safe="")
        return f'{prefix}/view?url={safe}"'

    def src_repl(match: re.Match[str]) -> str:
        prefix, link = match.group(1), match.group(2)
        absolute = urljoin(base_url, html.unescape(link))
        safe = quote(absolute, safe="")
        return f'{prefix}/asset?url={safe}"'

    no_script = re.sub(r"<script.*?>.*?</script>", "", raw_html, flags=re.IGNORECASE | re.DOTALL)
    no_base = re.sub(r"<base[^>]*>", "", no_script, flags=re.IGNORECASE)
    rewritten_href = re.sub(r'(href=["\'])([^"\']+)["\']', href_repl, no_base, flags=re.IGNORECASE)
    rewritten_src = re.sub(r'(src=["\'])([^"\']+)["\']', src_repl, rewritten_href, flags=re.IGNORECASE)
    return rewritten_src


def make_error_page(message: str) -> bytes:
    safe = html.escape(message)
    page = f"""<!doctype html><html><head><meta charset=\"utf-8\" /><title>Overmind Browser Error</title></head>
<body style=\"font-family:Arial;background:#111827;color:#f3f4f6;padding:20px\">
<h2>Impossible de charger la page</h2><p>{safe}</p><p><a href=\"/browser\" style=\"color:#93c5fd\">Retour navigateur</a></p>
</body></html>"""
    return page.encode("utf-8")


class OvermindHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, payload: bytes, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(LANDING_PAGE.encode("utf-8"))
            return

        if parsed.path == "/search":
            self._send_html(SEARCH_PAGE.encode("utf-8"))
            return

        if parsed.path == "/browser":
            self._send_html(BROWSER_PAGE.encode("utf-8"))
            return

        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0].strip()
            self._send_json({"results": build_results(query) if query else []})
            return

        if parsed.path == "/view":
            target_raw = parse_qs(parsed.query).get("url", [""])[0]
            target = normalize_target_url(unquote(target_raw))
            if not target:
                self._send_html(make_error_page("URL invalide. Utilise http:// ou https://"), HTTPStatus.BAD_REQUEST)
                return
            try:
                raw_html, _ = fetch_remote_html(target)
                rewritten = _rewrite_links(raw_html, base_url=target)
                self._send_html(rewritten.encode("utf-8"), HTTPStatus.OK)
            except Exception as exc:
                self._send_html(make_error_page(str(exc)), HTTPStatus.BAD_GATEWAY)
            return

        if parsed.path == "/asset":
            target_raw = parse_qs(parsed.query).get("url", [""])[0]
            target = normalize_target_url(unquote(target_raw))
            if not target:
                self.send_error(HTTPStatus.BAD_REQUEST)
                return
            try:
                req = Request(target, headers={"User-Agent": "OvermindBrowser/0.1"})
                with urlopen(req, timeout=8) as response:
                    data = response.read()
                    content_type = response.headers.get("Content-Type", "application/octet-stream")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                self.send_error(HTTPStatus.BAD_GATEWAY)
            return

        self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def main() -> None:
    parser = argparse.ArgumentParser(description="Overmind local web demo + mini browser")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), OvermindHandler)
    print(f"Overmind UI: http://{args.host}:{args.port}")
    print("Open /browser for the mini browser UI")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
