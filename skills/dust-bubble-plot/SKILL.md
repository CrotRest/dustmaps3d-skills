---
name: dust-bubble-plot
description: Make "dust bubble" (尘泡绘) figures from the Wang et al. (2025) 3D dust map through dustmaps3d-backend — for a bubble or cavity centred on Galactic (l, b) with an angular diameter and a distance shell, draw orthographic dust-density maps of the near / middle / far shells side by side, plus a dust-density-versus-distance analysis of the bubble's inner disk against its surrounding annulus (with the fitted peak distance) and the disk/annulus schematic. Use when the user studies a superbubble, a shell, a cavity or a cloud ring and wants to see it in 3D dust or locate its distance, or says 尘泡绘 / 尘埃气泡 / 超泡 / 空洞 / 气泡距离 / bubble plot / dust bubble.
---

# Dust bubble plotter (dustmaps3d-backend)

Rendered by **dustmaps3d-backend** (https://github.com/SunnyHina/dustmaps3d-backend); this skill sends the requests and saves the PNGs. It is the same tool as the website's 尘泡绘 and the NADC "Bubble plotter".

## Backend

- Address: `DUSTMAPS_API` or `--api`; default `http://127.0.0.1:58123`. Check with `curl -s $DUSTMAPS_API/health/ready` (`"dust"` and `"dustmaps_fits"` must be true).
- The orthographic panels need Java + STILTS on the server. If the backend is not reachable, tell the user and point them to the backend README; do not substitute local plots.

## What it makes

Given centre (l, b), angular diameter D and a shell [d_min, d_max] with Δ = d_max − d_min:

| file | content |
| --- | --- |
| `near.png` | mean dust density (mag/kpc) in [d_min − Δ, d_min] |
| `mid.png` | the chosen shell [d_min, d_max] |
| `far.png` | [d_max, d_max + Δ], with the colour bar |
| `triptych.png` | the three joined at a common height (written when Pillow is installed) |
| `analysis.png` | mean dust density of the inner disk and of the annulus versus distance, their difference, and a Gaussian fit of the peak inside [d_min, d_max] |
| `schematic.png` | the geometry: inner disk radius 0.25 D, annulus 0.375–0.625 D |

All three maps use FOV = 2.5 D (capped at 180°) and, by default, a circle of diameter D marking the bubble. A bubble shows up as a ring of high density in the middle shell that is weaker in front of and behind it; the analysis peak gives its distance.

## Usage

```bash
python scripts/bubble_plot.py --l 209 --b -19.4 --diameter 8 --d 0.3 0.5 --out-dir orion
```

Options: `--sigma` (Gaussian smoothing, deg, default 0.1), `--norm` hist|linear|log (default log; log needs `--vmin` > 0), `--vmin/--vmax` (default 0.01 / 1 mag/kpc), `--cmap` (Spectral_r, viridis, plasma, inferno, magma, cividis, Greys, rainbow), `--no-mark`, `--mark-color`.

Constraints: d_min > 0; very large diameters make the analysis exceed the backend's 2,000,000-sample limit (that panel then fails with a 422 message — reduce D). A full run takes roughly 30–60 s because each orthographic panel is a STILTS render. The script prints the files written and any per-panel errors; show the triptych and the analysis to the user and report the peak distance from the analysis figure.

## Citation

Wang, T. et al. (2025), ApJS 280, 15, doi:10.3847/1538-4365/adea39; dustmaps3d package, doi:10.12149/101619.
