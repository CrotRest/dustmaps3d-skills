---
name: dust-extinction-query
description: Look up 3D dust extinction from the Wang et al. (2025) all-sky map (Gaia + LAMOST) with the `dustmaps3d` pip package, locally — cumulative E(B−V), dust density, E(B−V) uncertainty and the maximum reliable distance for one sightline or a whole CSV/FITS catalogue (Galactic l,b or equatorial RA,Dec plus distance in kpc), and turn E(B−V) into band extinction A_λ or colour excess with the Zhang et al. (2024/2023) reddening coefficients. Use when the user asks for extinction, reddening, E(B-V), dust along a line of sight, to deredden photometry, to add E(B-V) to a star catalogue, or says 查消光 / 查 E(B-V) / 三维消光 / 消光改正 / 红化改正 / 红化系数 / dustmaps3d.
---

# 3D dust extinction query (dustmaps3d)

Everything here runs on the user's machine with the published Python package; no server is needed.

## What the map gives

`dustmaps3d(l, b, d)` takes Galactic longitude `l` and latitude `b` in degrees and heliocentric distance `d` in kpc (array-likes of equal length) and returns four pandas Series:

| output | meaning | unit |
| --- | --- | --- |
| `EBV` | cumulative E(B−V) out to `d` | mag |
| `dust` | dust density d(E(B−V))/dx at `d` (numerically equal to mmag/pc) | mag/kpc |
| `sigma` | uncertainty estimate of E(B−V) | mag |
| `max_d` | maximum reliable distance of that sightline | kpc |

- `d = NaN` → the package substitutes that sightline's `max_d`.
- `d > max_d` → outside the model's reliable range; values are **extrapolated and not reliable**. Always tell the user when this happens.
- `l`, `b` must not be NaN. Equatorial input must be converted first (ICRS → Galactic with astropy); `scripts/query.py` does this.
- Resolution is HEALPix Nside = 1024 (~3.4′). Pure NumPy, ~100 s for 10⁸ stars on one core.

## Setup

```bash
pip install dustmaps3d
```

The package does not ship the ~400 MB data file. The first call downloads `data_v3.fits.gz` (NADC mirror first on Chinese-locale systems, GitHub Releases otherwise), unpacks it to `data_v3.fits` and caches it. Warn the user before the first run. If the download fails (e.g. connect timeout), download it by hand from
- NADC: https://nadc.china-vo.org/res/file_upload/download?id=51939
- GitHub: https://github.com/Grapeknight/dustmaps3d/releases/download/v3/data_v3.fits.gz

then gunzip it and put `data_v3.fits` in the cache directory the package prints on first call (`platformdirs.user_data_dir("dustmaps3d")`: `~/Library/Application Support/dustmaps3d/` on macOS, `~/.local/share/dustmaps3d/` on Linux, `%LOCALAPPDATA%\dustmaps3d\` on Windows).

## Workflow

1. Get coordinates and distances from the user. Ask for the frame if it is ambiguous (Galactic vs equatorial) and for units if distances might be pc or a parallax rather than kpc.
2. Single sightline:
   ```bash
   python scripts/query.py --l 120 --b 30 --d 1.5
   python scripts/query.py --ra 83.82 --dec -5.39            # no d → uses max_d
   ```
3. Catalogue (CSV or FITS binary table with columns `l,b,d` or `ra,dec,d`, case-insensitive; blank `d` = max reliable distance):
   ```bash
   python scripts/query.py --input stars.csv --output stars_ebv.csv
   python scripts/query.py --input stars.fits --output stars_ebv.fits
   ```
   The output keeps every input column and appends `E(B-V)_mag`, `dust_density_mmag_pc`, `sigma_mag`, `max_distance_kpc` (plus `l`, `b` for equatorial input) and a boolean `extrapolated` (d > max_d). These are the same columns as the website's batch tool.
4. Report numbers with their uncertainty and say which rows are extrapolated.

Inline use is fine for small jobs:

```python
from dustmaps3d import dustmaps3d
EBV, dust, sigma, max_d = dustmaps3d([120.0], [30.0], [1.5])
print(f"E(B-V) = {EBV.values[0]:.4f} ± {sigma.values[0]:.4f} mag (reliable to {max_d.values[0]:.2f} kpc)")
```

## Extinction and reddening corrections

E(B−V) only gives the colour excess in B−V. For another band or colour you need its reddening coefficient:

- m_λ,0 = m_λ,obs − A_λ = m_λ,obs − R_λ · E(B−V)
- (a−b)_0 = (a−b)_obs − E(a−b) = (a−b)_obs − R_(a−b) · E(B−V)

Two sources, both from the same group:

- **Zhang et al. (2024), ApJ 972, 207** — median Milky Way extinction curve from Gaia XP spectra (`pip install xp-extinction-toolkit==1.0`, needs `scipy<1.14`). More general: Johnson UBVR, Gaia BP/G/RP, SDSS, Pan-STARRS1, 2MASS, WISE W1/W2, plus any wavelength or custom passband within the curve's 0.29–5.1 µm. GALEX and WISE W3/W4 lie outside it (the toolkit returns NaN or a meaningless value) — use the 2023 model for those. Returns A_λ or E(a−b) in mag.
- **Zhang et al. (2023), ApJS 264, 14** — empirical coefficients (`pip install extinction-coefficient==1.8`). Narrower but more precise: GALEX, PS1, SDSS, Gaia, 2MASS, WISE, valid for E(B−V) 0–0.5 mag and Teff 4000–10000 K. Returns the dimensionless R. **These coefficients are built on SFD: multiply E(B−V) from this 3D map by 1/0.834 before using them** (Wang et al. 2025, Fig. 17).

```bash
python scripts/reddening.py --band GAIA3.G --ebv 0.3 --teff 5500                 # 2024, extinction
python scripts/reddening.py --color GAIA3.Gbp-GAIA3.Grp --ebv 0.3 --teff 5500    # 2024, reddening
python scripts/reddening.py --model 2023 --color BP-RP --ebv 0.3 --teff 5500 --from-3d-map
```

`--from-3d-map` applies the 1/0.834 factor for the 2023 model. Band names differ between the two models (`GAIA3.Gbp` vs `BP`, `SDSS.g` vs `g'`, `PS1.g` vs `g`); the script lists them with `--list`.

Without per-star Teff, a reasonable average coefficient uses E(B−V) = 0.3 mag (median of Gaia XP stars) and Teff = 5500 K (Sun-like). For precise work compute star by star.

## Citation

Ask the user to cite both:
- Wang, T. et al. (2025), An all-sky 3D dust map based on Gaia and LAMOST, ApJS 280, 15, doi:10.3847/1538-4365/adea39
- dustmaps3d: A Python package for easy access to the 3D dust map, doi:10.12149/101619

plus Zhang et al. (2024) or (2023) when their coefficients are used. Package: https://github.com/Grapeknight/dustmaps3d (MIT). A faster implementation with multiprocessing and a CLI: https://github.com/SunnyHina/dustmaps3d.
