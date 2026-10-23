"""Murder Channel viewer server. Run: python server.py  then open http://localhost:8765"""
import json
import mimetypes
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from murder.data_cast import CHARACTERS, HOSTS
from murder.data_world import ROOMS, ITEMS, SECRET_ROOMS, ESCAPE_ROUTES, COMMON_ITEMS
from murder.session import Game, STATE_DIR
from murder.world import build_edges

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
PORT = 8766
game = Game()


from murder.looks import describe as describe_looks


def world_payload():
    cur = game.load_current()
    rooms = {rid: {"name": r[0], "zone": r[1], "x": r[2], "y": r[3], "w": r[4], "h": r[5], "secret": rid in SECRET_ROOMS} for rid, r in ROOMS.items()}
    edges = [{"id": e["id"], "a": e["a"], "b": e["b"], "hidden": e["hidden"], "locked": e["locked"], "kind": e["kind"]}
             for e in build_edges()]
    chars = {cid: {"name": c["name"], "short": c["short"], "role": c["role"], "color": c["color"], "card": c.get("card", ""),
                   "home": c["home"], "gender": c["gender"], "pron": c.get("pron"),
                   "casting_slot": c.get("casting_slot", c["gender"]),
                   "birthday": c.get("birthday"), "height_cm": c.get("height_cm"), "weight_kg": c.get("weight_kg"), "origin": c["origin"], "age": c["age"],
                   "status": cur["agents"].get(cid, {}).get("status", "alive"), "looks": describe_looks(cid, c)}
             for cid, c in cur.get("cast", {}).items()}
    hosts = {hid: {"name": h["name"], "role": h["role"], "color": h["color"], "card": h["card"]} for hid, h in HOSTS.items()}
    items = {iid: {"name": i["name"], "tags": i.get("tags", [])} for iid, i in ITEMS.items()}
    items.update({iid: {"name": i["name"], "tags": i.get("tags", [])} for iid, i in cur.get("custom_items", {}).items()})
    from murder import rules as rulelib
    routes = {rid: {"title": r["title"], "steps": list(r["steps"])} for rid, r in ESCAPE_ROUTES.items()}
    return {"rooms": rooms, "edges": edges, "characters": chars, "hosts": hosts, "items": items, "common": COMMON_ITEMS, "rules": rulelib.catalog(), "routes": routes}


_PERC = {}


# ---- remote access: with --host the server listens on the network and asks for a password (the PC itself is never asked)
import hashlib
import hmac
import secrets
import time as _time
from urllib.parse import parse_qs as _pq

AUTH = {"password": None, "secret": secrets.token_bytes(24), "fails": {}}
LOGIN_PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Murder Channel</title>
<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0f1016;color:#e8eaf2;font:16px system-ui}
form{background:#181a24;border:1px solid #2d3145;border-radius:14px;padding:22px;width:min(320px,86vw)}h1{font-size:15px;color:#ff5fa2;letter-spacing:.08em;margin:0 0 14px}
input{width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #2d3145;background:#1f2230;color:#e8eaf2;font-size:16px}
button{margin-top:12px;width:100%;padding:10px;border:0;border-radius:8px;background:#3ee0d0;color:#062421;font-weight:700;font-size:16px}.e{color:#ff6b6b;margin-top:8px;font-size:13px;min-height:16px}</style>
<form method="post" action="/login"><h1>MURDER CHANNEL</h1><input type="password" name="password" placeholder="__PH__" autofocus autocomplete="current-password"__NUM__><button>Enter</button><div class="e">__ERR__</div></form>"""


MAX_TRIES = 5                 # wrong tries from one device before it is locked out
MAX_TRIES_ALL = 20            # wrong tries from all devices in an hour before everyone but the PC is locked out
LOCK_SECONDS = 900
REMOTE_FILE = os.path.join(STATE_DIR, "remote.json")


def is_pin():
    return bool(AUTH["password"]) and AUTH["password"].isdigit() and len(AUTH["password"]) == 4


def remote_auth():
    """The PIN and cookie secret, kept between runs so the phone stays logged in. A --password or MC_PASSWORD replaces the PIN."""
    try:
        saved = json.load(open(REMOTE_FILE, encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    pin = saved.get("pin") if str(saved.get("pin", "")).isdigit() and len(str(saved.get("pin"))) == 4 else f"{secrets.randbelow(10000):04d}"
    secret = saved.get("secret") or secrets.token_hex(24)
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        json.dump({"pin": pin, "secret": secret}, open(REMOTE_FILE, "w", encoding="utf-8"))
    except OSError:
        pass
    return pin, bytes.fromhex(secret)


def auth_token():
    return hmac.new(AUTH["secret"], AUTH["password"].encode(), hashlib.sha256).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def _is_local(self):
        return self.client_address[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1")

    def _authed(self):
        if not AUTH["password"] or self._is_local():
            return True
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "mc_auth" and hmac.compare_digest(v, auth_token()):
                return True
        return False

    def _login(self, post):
        ip = self.client_address[0]
        now = _time.time()
        fails = [t for t in AUTH["fails"].get(ip, []) if now - t < LOCK_SECONDS]
        AUTH["fails"][ip] = fails
        AUTH["all_fails"] = [t for t in AUTH.get("all_fails", []) if now - t < 3600]
        err = ""
        if post:
            n = int(self.headers.get("Content-Length", 0) or 0)
            pw = (_pq(self.rfile.read(n).decode("utf-8", "ignore")).get("password") or [""])[0].strip()
            if len(fails) >= MAX_TRIES or len(AUTH["all_fails"]) >= MAX_TRIES_ALL:
                err = "Too many tries. Wait fifteen minutes."
            elif hmac.compare_digest(pw.encode(), AUTH["password"].encode()):
                AUTH["fails"].pop(ip, None)
                self.send_response(303)
                self.send_header("Set-Cookie", f"mc_auth={auth_token()}; Path=/; HttpOnly; SameSite=Strict; Max-Age=2592000")
                self.send_header("Location", "/")
                self.end_headers()
                return
            else:
                fails.append(now)
                AUTH["all_fails"].append(now)
                _time.sleep(1)
                err = "Wrong PIN." if is_pin() else "Wrong password."
        data = (LOGIN_PAGE.replace("__ERR__", err).replace("__PH__", "PIN" if is_pin() else "Password")
                .replace("__NUM__", ' inputmode="numeric" pattern="[0-9]*" maxlength="4"' if is_pin() else "")).encode("utf-8")
        self.send_response(200 if not err else 401)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _gate(self, post):
        """True if the request may go on. Otherwise the login page, a redirect or a 401 has been sent."""
        path = urlparse(self.path).path
        if path == "/login" and AUTH["password"]:
            self._login(post)
            return False
        if self._authed():
            return True
        if path.startswith("/api/"):
            self._json({"ok": False, "error": "login required"}, 401)
        else:
            self.send_response(303)
            self.send_header("Location", "/login")
            self.end_headers()
        return False

    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        if self._gate(False):
            self._get()

    def do_POST(self):
        if self._gate(True):
            self._post()

    def _get(self):
        u = urlparse(self.path)
        path = u.path
        if path == "/api/world":
            return self._json(world_payload())
        if path == "/api/diagnostics":
            return self._json(game.diagnostic_report())
        if path == "/api/status":
            return self._json(game.status())
        if path == "/api/ticks":
            q = parse_qs(u.query)
            since = int(q.get("since", ["0"])[0])
            pos = q.get("pos", [None])[0]
            return self._json(game.ticks(since, int(pos) if pos not in (None, "") else None, int(q.get("pv", ["0"])[0] or 0)))
        if path == "/api/gridmap":
            from murder import gridmap as _gm
            return self._json({"ok": True, "custom": _gm.load_custom() is not None, "map": _gm.load_custom() or _gm.build_grid_map()})
        if path == "/api/scenario/generate":
            q = parse_qs(u.query)
            try:
                seed = q.get("seed", [""])[0] or str(__import__("time").time_ns() % 10 ** 6)
                return self._json({"ok": True, **game.generate_scenario(seed, int(q.get("difficulty", ["5"])[0] or 5), q.get("secrets", ["0"])[0] == "1")})
            except ValueError as e:
                return self._json({"ok": False, "error": str(e)}, 400)
        if path == "/api/scenario":
            return self._json({"ok": True, **game.get_scenario()})
        if path == "/api/tuning":
            return self._json({"ok": True, **game.get_tuning()})
        if path == "/api/perception":
            from murder.perception import Perception
            q = parse_qs(u.query)
            pc = _PERC.get("p") or _PERC.setdefault("p", Perception())
            org = (q.get("plane", ["ground"])[0], int(q.get("x", ["0"])[0]), int(q.get("y", ["0"])[0]))
            light, loud = q.get("light", ["lit"])[0], q.get("loud", ["normal"])[0]
            if light not in ("lit", "dim", "dark") or loud not in ("whisper", "quiet", "normal", "loud", "shout"):
                return self._json({"ok": False, "error": "bad light or loudness"}, 400)
            return self._json({"ok": True, "visible": [list(t) for t in pc.visible_tiles(org, light)],
                               "heard": [[t[1], t[2], round(v, 1)] for t, v in pc.hearing_field(org, loud).items() if t[0] == org[0]]})
        if path == "/api/chronicle":
            q = parse_qs(u.query)

            def one(k):
                v = q.get(k, [None])[0]
                return v if v not in (None, "") else None
            day = one("day")
            return self._json({"ok": True, "entries": game.chronicle(day=int(day) if day else None, who=one("who"), kind=one("kind"), cls=one("cls"), q=one("q"),
                                                                    gm=one("gm") != "0", limit=int(one("limit") or 400), after=int(one("after") or 0))})
        if path == "/api/previously":
            q = parse_qs(u.query)
            return self._json({"ok": True, "data": game.previously(int(q.get("day", ["0"])[0] or 0))})
        if path == "/api/export":
            q = parse_qs(u.query)
            day = q.get("day", [None])[0]
            try:
                text = game.export(int(day) if day not in (None, "", "all") else None).encode("utf-8")
            except ValueError as e:
                return self._json({"ok": False, "error": str(e)}, 400)
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="murder-channel-{"day" + day if day not in (None, "", "all") else "season"}.md"')
            self.send_header("Content-Length", str(len(text)))
            self.end_headers()
            self.wfile.write(text)
            return
        if path == "/":
            path = "/index.html"
        fp = os.path.normpath(os.path.join(STATIC, path.lstrip("/")))
        # Initials stand in for reference art until an original PNG is installed.
        if fp.startswith(os.path.join(STATIC, "portraits") + os.sep) and fp.endswith(".png") and not os.path.isfile(fp):
            fallback = fp[:-4] + ".svg"
            if os.path.isfile(fallback):
                fp = fallback
        if not fp.startswith(STATIC) or not os.path.isfile(fp):
            self.send_response(404)
            self.end_headers()
            return
        ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
        with open(fp, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _post(self):
        path = urlparse(self.path).path
        body = self._body()
        try:
            if path == "/api/start":
                game.start(int(body["day"]), body.get("mode", "live"), body.get("backend", "cli"), int(body.get("step", 2)),
                           bool(body.get("murders", True)), str(body.get("motive", ""))[:400], str(body.get("rule", "roulette")),
                           str(body.get("rule_text", ""))[:600],
                           str(body.get("mischief", "occasional")), bool(body.get("confessionals", True)), str(body.get("chaos", "normal")),
                           int(body.get("variation", 0) or 0), bool(body.get("lean", False)), int(body.get("call_cap", 0) or 0), bool(body.get("autodir", False)),
                           int(body.get("week_len", 0) or 0), bool(body.get("resume", False)))
                return self._json({"ok": True})
            if path == "/api/newcomer/develop":
                return self._json({"ok": True, "fields": game.develop_newcomer(body, body.get("backend") or "cli")})
            if path == "/api/gm":
                return self._json({"ok": True, "note": game.gm_action(body)})
            if path == "/api/gridmap/validate":
                from murder import gridmap as _gm
                return self._json({"ok": True, "problems": _gm.validate_edit(body.get("map") or {})})
            if path == "/api/gridmap/save":
                from murder import gridmap as _gm, gridnav as _gn
                probs = _gm.save_custom(body.get("map") or {})
                _gn._CACHE.clear()
                return self._json({"ok": not probs, "problems": probs})
            if path == "/api/gridmap/reset":
                from murder import gridmap as _gm, gridnav as _gn
                _gm.reset_custom()
                _gn._CACHE.clear()
                return self._json({"ok": True})
            if path == "/api/tuning":
                return self._json({"ok": True, **game.set_tuning(body.get("values") or {})})
            if path == "/api/scenario":
                game.set_scenario(body.get("scenario"))
                return self._json({"ok": True, "scenario": game.get_scenario()["scenario"]})
            if path == "/api/roll":
                return self._json({"ok": game.answer_roll(body.get("id", 0), body.get("answer"))})
            if path == "/api/rollprefs":
                return self._json({"ok": True, "prefs": game.set_roll_prefs(body.get("kinds"), body.get("timeout"))})
            if path == "/api/autodir":
                game.set_autodir(body.get("on"))
                return self._json({"ok": True})
            if path == "/api/slot":
                act, name = body.get("action"), body.get("name")
                if act == "save":
                    return self._json({"ok": True, "slot": game.save_slot(name)})
                if act == "load":
                    return self._json({"ok": True, "slot": game.load_slot(name)})
                if act == "delete":
                    game.delete_slot(name)
                    return self._json({"ok": True})
                if act == "daystart":
                    return self._json({"ok": True, "day": game.goto_day_start(body.get("day"))})
                raise ValueError("Unknown save action.")
            if path == "/api/rewind":
                return self._json({"ok": True, "day": game.rewind()})
            if path == "/api/newcomer":
                cid = game.add_newcomer(body)
                return self._json({"ok": True, "id": cid})
            if path == "/api/ff":
                game.fast_forward()
                return self._json({"ok": True})
            if path == "/api/stop":
                game.stop()
                return self._json({"ok": True})
            if path == "/api/newgame":
                game.new_game(int(body.get("start_day", 3)), bool(body.get("keep_scenario", True)))
                return self._json({"ok": True})
        except Exception as e:
            return self._json({"ok": False, "error": str(e)}, 400)
        self._json({"ok": False, "error": "unknown endpoint"}, 404)


def local_ips():
    import socket
    out = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            out.add(info[4][0])
    except OSError:
        pass
    return sorted(i for i in out if not i.startswith("127."))


def main():
    remote = "--host" in sys.argv
    if remote:
        pw = os.environ.get("MC_PASSWORD") or (sys.argv[sys.argv.index("--password") + 1] if "--password" in sys.argv else "")
        pin, AUTH["secret"] = remote_auth()
        generated = not pw
        AUTH["password"] = pw or pin
    srv = ThreadingHTTPServer(("0.0.0.0" if remote else "127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Murder Channel viewer running at {url}  (Ctrl+C to stop)")
    if remote:
        print("Remote access is ON. On your phone open one of:")
        for ip in local_ips():
            print(f"    http://{ip}:{PORT}")
        print(f"PIN: {AUTH['password']}  (the same every run; delete state/remote.json for a new one)" if generated else f"Password: {AUTH['password']}")
        print("Only use this on your own Wi-Fi or over a private network such as Tailscale; never forward the port on your router.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
