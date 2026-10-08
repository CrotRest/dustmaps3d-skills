"""Draw a dust-density sky map with dustmaps3d-backend (POST /api/v2/plots/car or /plots/sin).

The map is the mean dust density ΔE(B-V)/Δd (mag/kpc) between d_min and d_max, at HEALPix
Nside 1024; directions whose shell midpoint lies beyond the reliable distance are blank.

Cartesian (longitude/latitude box):
    python sky_map.py car --lon 0 360 --lat -90 90 --d 0 3 --out allsky.png
Orthographic (centre + field of view; drawn by STILTS on the server):
    python sky_map.py sin --center 209 -19.4 --fov 20 --d 0.3 0.5 --norm log --vmin 0.01 --vmax 1 --mark

Backend address: --api or the DUSTMAPS_API environment variable (default http://127.0.0.1:58123).
Standard library only.
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
            sys.exit(f"backend error {e.code} on {path}: {detail}")
        except urllib.error.URLError as e:
            sys.exit(f"cannot reach the backend at {api} ({e.reason}). Start dustmaps3d-backend or set DUSTMAPS_API.")


def fetch(api, url, dest):
    full = url if url.startswith("http") else api + url
    with urllib.request.urlopen(full, timeout=120) as r:
        dest.write_bytes(r.read())


def style_args(ap, norm, vmin, vmax):
    ap.add_argument("--d", nargs=2, type=float, metavar=("D_MIN", "D_MAX"), required=True, help="distance shell in kpc")
    ap.add_argument("--frame", choices=["galactic", "equatorial"], default="galactic")
    ap.add_argument("--sigma", type=float, default=0.1, help="Gaussian smoothing in degrees (0-10)")
    ap.add_argument("--norm", choices=["hist", "linear", "log"], default=norm)
    ap.add_argument("--vmin", type=float, default=vmin)
    ap.add_argument("--vmax", type=float, default=vmax)
    ap.add_argument("--cmap", choices=COLORMAPS, default="Spectral_r")
    ap.add_argument("--out", type=Path, help="PNG path (default: a name built from the parameters)")
    ap.add_argument("--api", default=os.environ.get("DUSTMAPS_API", "http://127.0.0.1:58123"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    car = sub.add_parser("car", help="Cartesian longitude/latitude box")
    car.add_argument("--lon", nargs=2, type=float, default=[0, 360], metavar=("MIN", "MAX"))
    car.add_argument("--lat", nargs=2, type=float, default=[-90, 90], metavar=("MIN", "MAX"))
    style_args(car, "hist", 0.0, 2.0)
    sin = sub.add_parser("sin", help="orthographic view around a centre")
    sin.add_argument("--center", nargs=2, type=float, required=True, metavar=("LON", "LAT"))
    sin.add_argument("--fov", type=float, required=True, help="field of view in degrees (0-360]")
    sin.add_argument("--mark", action="store_true", help="draw a circle of diameter FOV/2.5 at the centre")
    sin.add_argument("--mark-color", choices=MARK_COLORS, default="black")
    style_args(sin, "log", 0.01, 1.0)
    a = ap.parse_args()

    d_min, d_max = a.d
    if not (0 <= d_min < d_max):
        ap.error("need 0 <= D_MIN < D_MAX (kpc)")
    if a.vmin >= a.vmax or (a.norm == "log" and a.vmin <= 0):
        ap.error("need vmin < vmax, and vmin > 0 for --norm log")
    body = {"coord_system": a.frame, "d_min": d_min, "d_max": d_max, "smoothing_sigma": a.sigma,
            "vmin": a.vmin, "vmax": a.vmax, "norm": a.norm, "colormap": a.cmap}
    if a.kind == "car":
        body.update(lon_min=a.lon[0], lon_max=a.lon[1], lat_min=a.lat[0], lat_max=a.lat[1])
        name = f"dust_car_l{a.lon[0]:g}-{a.lon[1]:g}_b{a.lat[0]:g}-{a.lat[1]:g}_d{d_min:g}-{d_max:g}.png"
    else:
        body.update(lon_center=a.center[0], lat_center=a.center[1], fov=a.fov, mark_region=a.mark, mark_color=a.mark_color)
        name = f"dust_sin_{a.center[0]:g}_{a.center[1]:g}_fov{a.fov:g}_d{d_min:g}-{d_max:g}.png"
    api = a.api.rstrip("/")
    t0 = time.time()
    result = post(api, f"/api/v2/plots/{a.kind}", body)
    out = a.out or Path(name)
    fetch(api, result["url"], out)
    print(json.dumps({"png": str(out), "seconds": round(time.time() - t0, 1), "request": body,
                      "shows": f"mean dust density between {d_min:g} and {d_max:g} kpc (mag/kpc)"}, indent=2))


if __name__ == "__main__":
    main()
