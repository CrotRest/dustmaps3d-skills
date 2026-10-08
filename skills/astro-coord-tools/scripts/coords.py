"""Convert sky positions between equatorial (ICRS), Galactic, ecliptic and heliocentric XYZ, with astropy.

Single position (angles in degrees, or sexagesimal strings for ICRS):
    python coords.py icrs 83.82 -5.39
    python coords.py icrs "05h35m16.8s" "-05d23m24s" --d 0.41
    python coords.py galactic 209.01 -19.38 --d 0.4
    python coords.py ecliptic 82.98 -28.68
    python coords.py xyz -0.33 -0.18 -0.13            # heliocentric Galactic Cartesian, kpc

Catalogue (CSV with ra,dec / l,b / lambda,beta / x,y,z columns, optional d):
    python coords.py icrs --input stars.csv --output stars_coords.csv

Conventions match the website's 04 tools: ICRS (J2000); ecliptic = astropy BarycentricMeanEcliptic,
equinox J2000 (obliquity 23.4392911°); XYZ is heliocentric along Galactic (l=0, b=0), (l=90°, b=0)
and the north Galactic pole, in the unit of d (kpc by default).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import BarycentricMeanEcliptic, CartesianRepresentation, Galactic, SkyCoord

ECL = BarycentricMeanEcliptic(equinox="J2000")
INPUT_COLUMNS = {"icrs": ("ra", "dec"), "galactic": ("l", "b"), "ecliptic": ("lambda", "beta"), "xyz": ("x", "y", "z")}


def build(frame, a, b, c=None, d=None):
    """SkyCoord from inputs in `frame`; `d` (kpc) is optional except for xyz."""
    dist = None if d is None else np.asarray(d, float) * u.kpc
    if frame == "xyz":
        rep = CartesianRepresentation(np.asarray(a, float), np.asarray(b, float), np.asarray(c, float), unit=u.kpc)
        return SkyCoord(rep, frame=Galactic())
    if frame == "icrs":
        unit = (u.hourangle, u.deg) if isinstance(a, str) and any(ch in a for ch in "hH:") else (u.deg, u.deg)
        return SkyCoord(a, b, unit=unit, frame="icrs", distance=dist)
    if frame == "galactic":
        return SkyCoord(l=np.asarray(a, float) * u.deg, b=np.asarray(b, float) * u.deg, frame="galactic", distance=dist)
    return SkyCoord(lon=np.asarray(a, float) * u.deg, lat=np.asarray(b, float) * u.deg, frame=ECL, distance=dist)


def describe(c, has_distance):
    eq, gal, ecl = c.icrs, c.galactic, c.transform_to(ECL)
    out = {
        "ra_deg": eq.ra.deg, "dec_deg": eq.dec.deg,
        "ra_hms": eq.ra.to_string(unit=u.hourangle, sep="hms", precision=3),
        "dec_dms": eq.dec.to_string(unit=u.deg, sep="dms", precision=2, alwayssign=True),
        "l_deg": gal.l.deg, "b_deg": gal.b.deg,
        "lambda_deg": ecl.lon.deg, "beta_deg": ecl.lat.deg,
    }
    if has_distance:
        xyz = gal.cartesian
        out.update(d_kpc=gal.distance.to_value(u.kpc), x_kpc=xyz.x.to_value(u.kpc),
                   y_kpc=xyz.y.to_value(u.kpc), z_kpc=xyz.z.to_value(u.kpc))
    return out


def convert_catalogue(frame, src, dst):
    import pandas as pd

    df = pd.read_csv(src)
    cols = {c.lower().strip(): c for c in df.columns}
    need = INPUT_COLUMNS[frame]
    missing = [n for n in need if n not in cols]
    if missing:
        sys.exit(f"{src} lacks columns {missing} for frame {frame}")
    values = [df[cols[n]].to_numpy(float) for n in need]
    d = df[cols["d"]].to_numpy(float) if "d" in cols and frame != "xyz" else None
    c = build(frame, *values) if frame == "xyz" else build(frame, values[0], values[1], d=d)
    res = describe(c, frame == "xyz" or d is not None)
    for k, v in res.items():
        df[k] = v
    df.to_csv(dst, index=False)
    print(f"wrote {len(df)} rows to {dst}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frame", choices=list(INPUT_COLUMNS))
    ap.add_argument("values", nargs="*", help="two angles (or x y z for xyz)")
    ap.add_argument("--d", type=float, help="distance in kpc, to also get heliocentric XYZ")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    # a leading space keeps argparse from reading sexagesimal values such as -05d23m24s as options
    a = ap.parse_args([" " + t if re.match(r"^-\d", t) and not re.fullmatch(r"-[\d.]+(e-?\d+)?", t) else t for t in sys.argv[1:]])
    a.values = [v.strip() for v in a.values]

    if a.input:
        convert_catalogue(a.frame, a.input, a.output or a.input.with_name(f"{a.input.stem}_coords.csv"))
        return
    n = 3 if a.frame == "xyz" else 2
    if len(a.values) != n:
        ap.error(f"{a.frame} needs {n} values")
    if a.frame == "xyz":
        c = build("xyz", *map(float, a.values))
    elif a.frame == "icrs":
        c = build("icrs", a.values[0], a.values[1], d=a.d)
    else:
        c = build(a.frame, float(a.values[0]), float(a.values[1]), d=a.d)
    res = describe(c, a.frame == "xyz" or a.d is not None)
    print(json.dumps({k: (round(v, 9) if isinstance(v, float) else v) for k, v in res.items()}, indent=2))


if __name__ == "__main__":
    main()
