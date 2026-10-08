---
name: astro-coord-tools
description: Small astronomy conversions with astropy — sky positions between equatorial (ICRS RA/Dec, decimal or sexagesimal), Galactic (l, b), ecliptic (λ, β) and heliocentric Galactic XYZ (with a distance), for one target or a CSV catalogue; and angular diameter ↔ physical diameter at a given distance. Use when the user asks to convert coordinates, turn RA/Dec into l/b (e.g. before a dust-extinction query), get a star's XYZ position, or how big an object is in arcmin or in pc, or says 坐标换算 / 赤道转银道 / 黄道坐标 / 日心直角坐标 / 角直径 / 物理尺度 / 角尺度换算.
---

# Astronomy utilities: coordinates and angular size

Local, no server. Needs `astropy` (and `pandas` for catalogues). These are the website's 04 tools; the conventions are the same.

## Coordinates

```bash
python scripts/coords.py icrs 83.82 -5.39
python scripts/coords.py icrs "05h35m16.8s" "-05d23m24s" --d 0.41
python scripts/coords.py galactic 209.01 -19.38 --d 0.4
python scripts/coords.py ecliptic 82.98 -28.68
python scripts/coords.py xyz -0.33 -0.18 -0.13
python scripts/coords.py icrs --input stars.csv            # columns ra,dec[,d]
```

Output: RA/Dec in degrees and sexagesimal, Galactic l/b, ecliptic λ/β, and — when a distance is given — d and heliocentric XYZ.

Conventions:
- Equatorial = ICRS (J2000). Sexagesimal RA is read as hours when it contains `h` or `:`.
- Ecliptic = astropy `BarycentricMeanEcliptic(equinox="J2000")` (obliquity 23.4392911°).
- XYZ is heliocentric Galactic Cartesian: x toward (l, b) = (0°, 0°), y toward (90°, 0°), z toward the north Galactic pole, in kpc. It is not Galactocentric.
- Catalogue columns are case-insensitive: `ra,dec` / `l,b` / `lambda,beta` / `x,y,z`, plus optional `d` (kpc). Results are appended as new columns.

To get the dust extinction of the converted position, hand l, b (and d) to the `dust-extinction-query` skill.

## Angular ↔ physical size

```bash
python scripts/angular_size.py size-to-angle --size 10 --size-unit pc --distance 0.4 --distance-unit kpc
python scripts/angular_size.py angle-to-size --angle 8 --angle-unit deg --distance 400 --distance-unit pc
```

Exact relations θ = 2·atan(D / 2d) and D = 2·d·tan(θ / 2), not the small-angle approximation. Length units pc, kpc, Mpc, ly, au, km; angle units deg, arcmin, arcsec, mas, rad.
