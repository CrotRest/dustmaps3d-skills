"""Dust-bubble figures around one sightline with dustmaps3d-backend (the "尘泡绘" tool).

For a bubble centred on (l, b) with angular diameter D and a distance shell [d_min, d_max]:
  near.png / mid.png / far.png  orthographic dust-density maps of [d_min-Δ, d_min], [d_min, d_max],
                                [d_max, d_max+Δ] (Δ = d_max - d_min), FOV = 2.5 D (≤ 180°)
  triptych.png                  the three side by side (needs Pillow; skipped otherwise)
  analysis.png                  inner-disk vs annulus dust density along distance, with the fitted peak
  schematic.png                 the inner disk / annulus geometry used by the analysis

    python bubble_plot.py --l 209 --b -19.4 --diameter 8 --d 0.3 0.5 --out-dir orion_bubble

Backend address: --api or DUSTMAPS_API (default http://127.0.0.1:58123). Standard library + optional Pillow.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

COLORMAPS = ["Spectral_r", "viridis", "plasma", "inferno", "magma", "cividis", "Greys", "rainbow"]
MARK_COLORS = ["black", "white", "red", "blue", "green", "yellow"]


def post(api, path, body, retries=6):
    """POST JSON; waits and retries while the backend reports it is at capacity (503 + Retry-After)."""
    req = urllib.request.Request(api + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code == 503 and "capacity" in detail and attempt < retries - 1:
                time.sleep(float(e.headers.get("Retry-After", 5)))
                continue
            raise RuntimeError(f"backend error {e.code} on {path}: {detail}") from None
        except urllib.error.URLError as e:
            sys.exit(f"cannot reach the backend at {api} ({e.reason}). Start dustmaps3d-backend or set DUSTMAPS_API.")


def fetch(api, url, dest):
    full = url if url.startswith("http") else api + url
    with urllib.request.urlopen(full, timeout=120) as r:
        dest.write_bytes(r.read())


def triptych(paths, dest):
    """Join the panels at a common height, as the website and the NADC page do."""
    try:
        from PIL import Image
    except ImportError:
        return False
    imgs = [Image.open(p).convert("RGB") for p in paths]
    h = max(i.height for i in imgs)
    imgs = [i.resize((round(i.width * h / i.height), h)) for i in imgs]
    canvas = Image.new("RGB", (sum(i.width for i in imgs), h), "white")
    x = 0
    for i in imgs:
        canvas.paste(i, (x, 0))
        x += i.width
    canvas.save(dest)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--l", type=float, required=True, help="Galactic longitude of the bubble centre, deg")
    ap.add_argument("--b", type=float, required=True, help="Galactic latitude of the bubble centre, deg")
    ap.add_argument("--diameter", type=float, required=True, help="angular diameter of the bubble, deg")
    ap.add_argument("--d", nargs=2, type=float, required=True, metavar=("D_MIN", "D_MAX"), help="distance shell, kpc (D_MIN > 0)")
    ap.add_argument("--sigma", type=float, default=0.1, help="Gaussian smoothing, deg")
    ap.add_argument("--norm", choices=["hist", "linear", "log"], default="log")
    ap.add_argument("--vmin", type=float, default=0.01)
    ap.add_argument("--vmax", type=float, default=1.0)
    ap.add_argument("--cmap", choices=COLORMAPS, default="Spectral_r")
    ap.add_argument("--no-mark", action="store_true", help="do not draw the bubble circle")
    ap.add_argument("--mark-color", choices=MARK_COLORS, default="black")
    ap.add_argument("--out-dir", type=Path, help="default: bubble_l<l>_b<b>")
    ap.add_argument("--api", default=os.environ.get("DUSTMAPS_API", "http://127.0.0.1:58123"))
    a = ap.parse_args()

    d_min, d_max = a.d
    if not (0 < d_min < d_max):
        ap.error("need 0 < D_MIN < D_MAX (kpc)")
    if a.diameter <= 0 or not -90 <= a.b <= 90:
        ap.error("need diameter > 0 and -90 <= b <= 90")
    if a.vmin >= a.vmax or (a.norm == "log" and a.vmin <= 0):
        ap.error("need vmin < vmax, and vmin > 0 for --norm log")
    api = a.api.rstrip("/")
    out = a.out_dir or Path(f"bubble_l{a.l:g}_b{a.b:g}")
    out.mkdir(parents=True, exist_ok=True)

    delta = d_max - d_min
    base = {"coord_system": "galactic", "lon_center": a.l, "lat_center": a.b, "fov": min(a.diameter * 2.5, 180),
            "bubble_diameter": a.diameter, "mark_region": not a.no_mark, "mark_color": a.mark_color,
            "smoothing_sigma": a.sigma, "vmin": a.vmin, "vmax": a.vmax, "norm": a.norm, "colormap": a.cmap}
    shells = {
        "near": {**base, "d_min": max(0.0, d_min - delta), "d_max": d_min, "show_color_bar": False},
        "mid": {**base, "d_min": d_min, "d_max": d_max, "show_color_bar": False},
        "far": {**base, "d_min": d_max, "d_max": d_max + delta, "show_color_bar": True},
    }
    extra = {
        "analysis": ("/api/v2/bubbles/analyze", {"l": a.l, "b": a.b, "d": (d_min + d_max) / 2, "d_low": d_min,
                                                  "d_up": d_max, "diameter": a.diameter}),
        "schematic": ("/api/v2/bubbles/schematic", {"diameter": a.diameter}),
    }
    t0 = time.time()
    files, errors = {}, {}
    # The backend serves one computation at a time, so plain sequential calls are as fast as any.
    jobs = [(k, "/api/v2/plots/sin", body) for k, body in shells.items()] + [(k, *v) for k, v in extra.items()]
    for key, path, body in jobs:
        try:
            dest = out / f"{key}.png"
            fetch(api, post(api, path, body)["url"], dest)
            files[key] = str(dest)
        except RuntimeError as e:
            errors[key] = str(e)
    if all(k in files for k in shells) and triptych([files[k] for k in shells], out / "triptych.png"):
        files["triptych"] = str(out / "triptych.png")
    print(json.dumps({"files": files, "errors": errors, "seconds": round(time.time() - t0, 1),
                      "shells_kpc": {k: [round(v["d_min"], 4), round(v["d_max"], 4)] for k, v in shells.items()},
                      "fov_deg": base["fov"]}, indent=2, ensure_ascii=False))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
