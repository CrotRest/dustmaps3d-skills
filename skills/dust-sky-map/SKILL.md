---
name: dust-sky-map
description: Draw sky maps of interstellar dust from the Wang et al. (2025) 3D dust map through dustmaps3d-backend — the mean dust density (ΔE(B−V)/Δd, mag/kpc) in a chosen distance shell, as a Cartesian longitude/latitude map (any box up to the whole sky, Galactic or equatorial) or an orthographic view around a centre with a given field of view. Use when the user wants an extinction / dust / reddening map of a sky region or the whole sky at some distance range, a figure of a molecular-cloud region in a distance slice, or says 画消光图 / 全天消光图 / 尘埃分布图 / 天区尘埃图 / 某个距离层的尘埃 / dust map plot.
---

# Dust sky maps (dustmaps3d-backend)

The maps are rendered by **dustmaps3d-backend** (https://github.com/SunnyHina/dustmaps3d-backend, FastAPI). This skill only sends requests and saves the PNG; the backend must be running somewhere the user can reach.

## Backend

- Address: `DUSTMAPS_API` environment variable or `--api`; default `http://127.0.0.1:58123`.
- Check it first: `curl -s $DUSTMAPS_API/health/ready` should report `"dust": true`.
- If nothing answers, tell the user the backend is not running and point them to the backend README (Python 3.11/3.12, `uv sync --locked`, a `data.parquet` converted from the dustmaps3d `data_v3.fits`, Java + STILTS for orthographic maps, `uvicorn dustmaps_backend.main:app --port 58123 --workers 1`). Do not try to fake a map locally.

## What is drawn

Both projections show the **mean dust density between d_min and d_max**: (E(B−V)(d_max) − E(B−V)(d_min)) / (d_max − d_min), in mag/kpc, on the Nside = 1024 HEALPix grid (~3.4′), optionally Gaussian-smoothed. Directions whose shell midpoint lies beyond that sightline's maximum reliable distance are left blank. This is a density map, not cumulative E(B−V) — say so when presenting it.

## Usage

```bash
# whole sky, Cartesian, 0–3 kpc (≈20–30 s, 5000+ px wide PNG)
python scripts/sky_map.py car --lon 0 360 --lat -90 90 --d 0 3 --out allsky_0-3kpc.png

# a box in equatorial coordinates
python scripts/sky_map.py car --frame equatorial --lon 70 100 --lat -20 10 --d 0.3 0.6 --norm log --vmin 0.01 --vmax 1

# orthographic view, 20° field around Orion, with a marker circle (STILTS, ≈5–15 s)
python scripts/sky_map.py sin --center 209 -19.4 --fov 20 --d 0.3 0.5 --mark
```

Parameters (same as the website's sky-map tool and the NADC form):

| option | meaning | default |
| --- | --- | --- |
| `--d D_MIN D_MAX` | distance shell, kpc (`0 <= D_MIN < D_MAX`) | required |
| `--frame` | `galactic` or `equatorial` | galactic |
| `--lon/--lat MIN MAX` (car) | box in degrees; `--lon 0 360 --lat -90 90` is the whole sky | whole sky |
| `--center LON LAT`, `--fov` (sin) | centre and field of view in degrees | required |
| `--mark`, `--mark-color` (sin) | circle of diameter FOV/2.5 at the centre | off, black |
| `--sigma` | Gaussian smoothing, degrees (0–10) | 0.1 |
| `--norm` | `hist`, `linear` or `log` (log needs `--vmin` > 0) | car: hist, sin: log |
| `--vmin/--vmax` | colour range, mag/kpc | car 0–2, sin 0.01–1 |
| `--cmap` | Spectral_r, viridis, plasma, inferno, magma, cividis, Greys, rainbow | Spectral_r |

The script prints the PNG path and the exact request. Show the image to the user and state the shell and units. A 503 "capacity" reply means the backend is busy; the script waits and retries. A 503 about a dataset means the backend lacks data (orthographic maps also need STILTS on the server).

For cumulative E(B−V) along individual sightlines use the `dust-extinction-query` skill instead.

## Citation

Wang, T. et al. (2025), ApJS 280, 15, doi:10.3847/1538-4365/adea39; dustmaps3d package, doi:10.12149/101619.
