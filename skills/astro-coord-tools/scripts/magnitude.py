"""Apparent <-> absolute magnitude with distance (or parallax) and extinction.

    m − M = 5·log10(d / 10 pc) + A_λ

    python magnitude.py to-abs  --m 12 --distance 1 --distance-unit kpc --A 0.3
    python magnitude.py to-app  --M 4.83 --distance 10 --distance-unit pc
    python magnitude.py to-dist --m 15 --M 4.5 --A 0.5
    python magnitude.py to-abs  --m 12 --distance 2 --distance-unit mas --from-3d-map --l 30.5 --b 0.6 --band GAIA3.G

Distance units: pc, kpc, ly, or mas for a parallax (d = 1000 / ϖ, no bias correction).
Extinction: none, --A in mag, or --from-3d-map: E(B−V) at (l, b) or (ra, dec) and that distance
from the Wang et al. (2025) map (`pip install dustmaps3d`), turned into A_λ for --band with the
Zhang et al. (2024) XP toolkit (`pip install xp-extinction-toolkit==1.0`, scipy<1.14) at --teff.
--from-3d-map needs a distance, so it is not available with to-dist.
Same formulas as the website's 05 magnitude tool.
"""
import argparse
import json
import math
import warnings

LY_PER_PC = 3.261563777
# Zhang et al. (2024) bands that its curve (0.29–5.1 µm) covers: GALEX and WISE W3/W4 fall outside
BANDS_2024 = ["Johnson.U", "Johnson.B", "Johnson.V", "Johnson.R", "GAIA3.Gbp", "GAIA3.G", "GAIA3.Grp",
              "SDSS.u", "SDSS.g", "SDSS.r", "SDSS.i", "SDSS.z", "PS1.g", "PS1.r", "PS1.i", "PS1.z", "PS1.y",
              "2MASS.J", "2MASS.H", "2MASS.Ks", "WISE.W1", "WISE.W2", "440", "550"]


def distance_pc(value, unit):
    if not value > 0:
        raise ValueError("distance / parallax must be > 0")
    return {"pc": value, "kpc": value * 1e3, "ly": value / LY_PER_PC, "mas": 1e3 / value}[unit]


def modulus(d_pc):
    return 5 * math.log10(d_pc / 10)


def map_extinction(a, d_pc):
    """E(B−V) from the 3D map at (position, d) → A_λ for a.band from the Zhang et al. (2024) curve."""
    import numpy as np
    from dustmaps3d import dustmaps3d
    from xp_extinction_toolkit import ExtinctionToolkit

    l, b = a.l, a.b
    if l is None:
        from astropy import units as u
        from astropy.coordinates import SkyCoord

        g = SkyCoord(ra=a.ra * u.deg, dec=a.dec * u.deg, frame="icrs").galactic
        l, b = g.l.deg, g.b.deg
    ebv, _, sigma, max_d = (float(np.asarray(x)[0]) for x in dustmaps3d([l], [b], [d_pc / 1e3]))
    tool = ExtinctionToolkit()
    e4455 = tool.Cal_E4455(ebv=max(ebv, 0), Teff=a.teff)
    A = float(tool.star_ext([a.band], E4455=e4455, Teff=[a.teff])[a.band][0])
    info = {"l": l, "b": b, "ebv": ebv, "ebv_sigma": sigma, "max_distance_kpc": max_d, "band": a.band,
            "teff": a.teff, "A_mag": A}
    if d_pc / 1e3 > max_d:
        info["warning"] = f"d exceeds this sightline's maximum reliable distance {max_d:.2f} kpc; E(B-V) is extrapolated"
    return A, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["to-abs", "to-app", "to-dist"])
    ap.add_argument("--m", type=float, help="apparent magnitude")
    ap.add_argument("--M", type=float, help="absolute magnitude")
    ap.add_argument("--distance", type=float, help="distance, or parallax with --distance-unit mas")
    ap.add_argument("--distance-unit", choices=["pc", "kpc", "ly", "mas"], default="pc")
    ap.add_argument("--A", type=float, help="extinction A_λ in mag (default 0)")
    ap.add_argument("--from-3d-map", action="store_true", help="take A_λ from the 3D map + Zhang et al. (2024)")
    ap.add_argument("--l", type=float)
    ap.add_argument("--b", type=float)
    ap.add_argument("--ra", type=float)
    ap.add_argument("--dec", type=float)
    ap.add_argument("--band", choices=BANDS_2024, default="GAIA3.G")
    ap.add_argument("--teff", type=float, default=5500, help="K, for the 2024 coefficient (default 5500)")
    a = ap.parse_args()

    if a.from_3d_map:
        if a.A is not None:
            ap.error("give either --A or --from-3d-map")
        if a.mode == "to-dist":
            ap.error("--from-3d-map needs a distance; give --A when solving for distance")
        if (a.l is None) == (a.ra is None) or (a.l is not None and a.b is None) or (a.ra is not None and a.dec is None):
            ap.error("--from-3d-map needs --l --b or --ra --dec")
    need = {"to-abs": ["m", "distance"], "to-app": ["M", "distance"], "to-dist": ["m", "M"]}[a.mode]
    missing = [f"--{k.replace('_', '-')}" for k in need if getattr(a, k) is None]
    if missing:
        ap.error(f"{a.mode} needs {' '.join(missing)}")

    warnings.filterwarnings("ignore")
    out = {"mode": a.mode}
    if a.mode == "to-dist":
        A = a.A or 0.0
        mu = a.m - a.M - A
        d = 10 ** (mu / 5 + 1)
        out.update({"A_mag": A, "distance_pc": d, "distance_kpc": d / 1e3, "distance_ly": d * LY_PER_PC,
                    "parallax_mas": 1e3 / d, "distance_modulus": mu})
    else:
        try:
            d = distance_pc(a.distance, a.distance_unit)
        except ValueError as e:
            ap.error(str(e))
        if a.from_3d_map:
            A, info = map_extinction(a, d)
            out["extinction"] = info
        else:
            A = a.A or 0.0
        mu = modulus(d)
        out.update({"distance_pc": d, "distance_modulus": mu, "A_mag": A})
        if a.mode == "to-abs":
            out["M"] = a.m - mu - A
        else:
            out["m"] = a.M + mu + A
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
