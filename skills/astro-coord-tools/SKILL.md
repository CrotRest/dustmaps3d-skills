---
name: astro-coord-tools
description: Small astronomy conversions with astropy — sky positions between equatorial (ICRS RA/Dec, decimal or sexagesimal), Galactic (l, b), ecliptic (λ, β) and heliocentric Galactic XYZ (with a distance), for one target or a CSV catalogue; angular diameter ↔ physical diameter at a given distance; and apparent ↔ absolute magnitude with distance or parallax and extinction (typed, or E(B−V) from the Wang et al. 2025 3D dust map turned into A_λ with Zhang et al. 2024). Use when the user asks to convert coordinates, turn RA/Dec into l/b (e.g. before a dust-extinction query), get a star's XYZ position, how big an object is in arcmin or in pc, a star's absolute magnitude, the apparent magnitude at some distance, or the distance from m and M, or says 坐标换算 / 赤道转银道 / 黄道坐标 / 日心直角坐标 / 角直径 / 物理尺度 / 角尺度换算 / 视星等 / 绝对星等 / 星等换算 / 距离模数.
---

# Astronomy utilities: coordinates, angular size and magnitudes

Local, no server. Needs `astropy` (and `pandas` for catalogues). These are the website's 05 tools; the conventions are the same.

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

## Apparent ↔ absolute magnitude

```bash
python scripts/magnitude.py to-abs  --m 12 --distance 1 --distance-unit kpc --A 0.3
python scripts/magnitude.py to-app  --M 4.83 --distance 2 --distance-unit mas         # parallax 2 mas
python scripts/magnitude.py to-dist --m 15 --M 4.5 --A 0.5
python scripts/magnitude.py to-abs  --m 12 --distance 1000 --from-3d-map --l 30.5 --b 0.6 --band GAIA3.G --teff 5500
```

m − M = 5·log10(d / 10 pc) + A_λ. Distance units pc, kpc, ly, or `mas` for a parallax (d = 1000 / ϖ, no bias correction — say so when the parallax is noisy). `to-dist` also prints the distance in kpc, ly, the parallax and the distance modulus.

Extinction is 0 by default, `--A` in mag, or `--from-3d-map`: E(B−V) at (l, b) or (ra, dec) and that distance from the Wang et al. (2025) map (`pip install dustmaps3d`, see the `dust-extinction-query` skill for the data download), turned into A_λ of `--band` at `--teff` (default 5500 K) with the Zhang et al. (2024) curve (`pip install xp-extinction-toolkit==1.0`, needs `scipy<1.14`). The JSON then also shows E(B−V) ± σ and warns when d is beyond the sightline's maximum reliable distance. `--from-3d-map` needs a distance, so `to-dist` takes `--A` only. Bands: Johnson UBVR, Gaia BP/G/RP (`GAIA3.Gbp`, `GAIA3.G`, `GAIA3.Grp`), `SDSS.ugriz`, `PS1.grizy`, `2MASS.J/H/Ks`, `WISE.W1/W2`, `440`, `550`. When the map is used, ask the user to cite Wang et al. (2025) and Zhang et al. (2024).
