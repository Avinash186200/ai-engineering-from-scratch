"""Minimal chat page on the standard library (no web framework needed).

    python day18_agent_testing/web/app.py          # http://127.0.0.1:8018
One Agent per browser session id, so multi-turn state carries over like in the YAML threads.
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fi_agent.agent import Agent  # noqa: E402
from fi_agent.tracing import Tracer, new_run_id  # noqa: E402

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Fixed-income agent</title>
<style>body{font-family:sans-serif;max-width:720px;margin:2em auto}#log div{margin:.4em 0}
.user{color:#036}.bot{color:#333}.tool{color:#888;font-size:.85em}</style></head><body>
<h1>Fixed-income agent (offline)</h1><div id="log"></div>
<form id="f"><input id="msg" size="60" autocomplete="off"><button id="send">Send</button></form>
<script>
const sid = Math.random().toString(36).slice(2);
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault(); const m = document.getElementById('msg'); const text = m.value; m.value = '';
  const log = document.getElementById('log');
  log.insertAdjacentHTML('beforeend', `<div class="user">you: ${text}</div>`);
  const r = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'},
                                  body: JSON.stringify({session_id: sid, message: text})});
  const j = await r.json();
  const bot = document.createElement('div'); bot.className = 'bot'; bot.textContent = 'agent: ' + j.answer;
  bot.setAttribute('data-testid', 'answer'); log.appendChild(bot);
  if (j.tool) { const t = document.createElement('div'); t.className = 'tool';
    t.textContent = `tool=${j.tool} params=${JSON.stringify(j.params)} turn_id=${j.turn_id}`; log.appendChild(t); }
};
</script></body></html>"""

RUN_ID = new_run_id()
TRACER = Tracer(RUN_ID)
SESSIONS: dict[str, list] = {}
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # keep test output quiet
        pass

    def _send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/chat":
            return self._send(404, "not found", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            sid, msg = str(body["session_id"]), str(body["message"])
        except (ValueError, KeyError):
            return self._send(422, json.dumps({"error": "need session_id and message"}), "application/json")
        with LOCK:
            entry = SESSIONS.setdefault(sid, [Agent(tracer=TRACER), 0])
            entry[1] += 1
            turn_id = f"web-{sid}:t{entry[1]}"
            res = entry[0].turn(msg, turn_id=turn_id)
        call = res.first_call or {}
        self._send(200, json.dumps({"answer": res.answer, "tool": call.get("name"), "params": call.get("params"),
                                    "run_id": RUN_ID, "turn_id": turn_id}), "application/json")


def make_server(port=8018):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    srv = make_server()
    print(f"http://127.0.0.1:{srv.server_port}  (run_id={RUN_ID})")
    srv.serve_forever()
