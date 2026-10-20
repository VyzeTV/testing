"""Comic panels through Atlas Cloud, with the cast portraits as references.

    python tools/comic.py docs/runs/seed11/comic/strip.json [--only a3,b2] [--redo] [--model seed]

--model sends the same prompts to another model (the fallback after a refusal); the spec's
"body_<model>" (e.g. "body_seed": {"size": "2496*1664"}) then replaces its "body".

Needs ATLASCLOUD_API_KEY. Panels already on disk are skipped (each call costs money);
the run stops at the first refusal so a bad prompt is not paid for twice.
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request
from PIL import Image

API = "https://api.atlascloud.ai/api/v1/model"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTRAITS = os.path.join(ROOT, "static", "portraits")
# name: (model id, field for the reference images, extra body, dollars per image as listed by /api/v1/models;
# the nano readme gives $0.05 per 1k image plus $0.00168 per reference, so the real charge may be higher)
MODELS = {
    "nano": ("google/nano-banana-2.1-developer/edit", "reference_images", {"aspect_ratio": "1:1", "resolution": "1k"}, 0.018),
    "seed": ("bytedance/seedream-v5.0-flash/edit", "images", {"size": "1536*1536"}, 0.018),
    "qwen": ("qwen/qwen-image-2.0/edit", "images", {}, 0.028),  # at most 3 references, prompt at most 800 characters
    # the readme's own prices: $0.06 at medium/1k plus $0.01 per input image
    "grok": ("xai/grok-imagine-image-2.0-developer/edit", "image_urls", {"resolution": "1k", "quality": "medium"}, 0.014),
}


def ref(cid, folder="."):
    """A portrait id, or an earlier panel's file (e.g. "b2.jpg") from the spec's folder."""
    path = os.path.join(folder, cid) if cid.endswith(".jpg") else os.path.join(PORTRAITS, cid + ".png")
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    buf = io.BytesIO()
    bg.convert("RGB").resize((512, 512), Image.LANCZOS).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def call(method, url, body=None):
    # Atlas Cloud's firewall rejects Python's default user agent (Cloudflare 1010).
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + os.environ["ATLASCLOUD_API_KEY"],
                                          "Content-Type": "application/json", "User-Agent": "murder-channel/1.0"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read()[:300]!r}"}


def generate(model, prompt, refs, out, folder=".", over=None):
    """One image; returns an error string or None. `over` replaces body fields (e.g. aspect_ratio for a full page)."""
    mid, field, extra, _ = MODELS[model]
    body = {"model": mid, "prompt": prompt, field: [ref(r, folder) for r in refs], "enable_base64_output": True, **extra, **(over or {})}
    r = call("POST", f"{API}/generateImage", body)
    if "data" not in r:
        return r.get("error") or r.get("msg") or str(r)[:300]
    pid = r["data"]["id"]
    for _ in range(100):
        time.sleep(3)
        d = call("GET", f"{API}/prediction/{pid}").get("data") or {}
        if d.get("status") in ("completed", "succeeded", "failed"):
            break
    if d.get("status") != "completed" or not d.get("outputs"):
        return d.get("error") or f"status {d.get('status')}"
    im = Image.open(io.BytesIO(base64.b64decode(d["outputs"][0].split(",", 1)[-1]))).convert("RGB")
    im.save(out, "JPEG", quality=88)
    return None


def main(argv):
    spec_path = argv[0]
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    spec = json.load(open(spec_path))
    folder = os.path.dirname(os.path.abspath(spec_path))
    model, style = spec["model"], spec["style"]
    body = spec.get("body", {})
    if "--model" in argv:
        model = argv[argv.index("--model") + 1]
        body = spec.get("body_" + model, {}) if model != spec["model"] else body
    spent = 0.0
    for strip in spec["strips"]:
        for p in strip["panels"]:
            if only and p["id"] not in only:
                continue
            out = os.path.join(folder, p["id"] + ".jpg")
            if os.path.exists(out) and "--redo" not in argv:
                continue
            err = generate(model, p["prompt"] + " " + style, p["refs"], out, folder, {**body, **p.get("body", {})})
            if err:
                print(f"{p['id']}: FAILED ({err}); stopping. Spent ${spent:.3f}")
                return 1
            spent += MODELS[model][3]
            print(f"{p['id']}: saved ({p['refs']}) ${spent:.3f} so far")
    print(f"done, spent ${spent:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
