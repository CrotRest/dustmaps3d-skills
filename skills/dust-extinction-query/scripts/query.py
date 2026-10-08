"""Query the Wang et al. (2025) 3D dust map with the `dustmaps3d` package.

Single sightline (Galactic or equatorial; omit --d to use the maximum reliable distance):
    python query.py --l 120 --b 30 --d 1.5
    python query.py --ra 83.82 --dec -5.39 --d 0.4

Catalogue (CSV or FITS with columns l,b,d or ra,dec,d — case-insensitive, blank d allowed):
    python query.py --input stars.csv --output stars_ebv.csv

Output columns: E(B-V)_mag, dust_density_mmag_pc, sigma_mag, max_distance_kpc, extrapolated
(plus l, b for equatorial input). `extrapolated` marks d > max_distance: those values are
outside the model's reliable range.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RESULT_COLUMNS = ["E(B-V)_mag", "dust_density_mmag_pc", "sigma_mag", "max_distance_kpc"]


def to_galactic(ra, dec):
    from astropy import units as u
    from astropy.coordinates import SkyCoord

    g = SkyCoord(ra=np.asarray(ra, float) * u.deg, dec=np.asarray(dec, float) * u.deg, frame="icrs").galactic
    return g.l.deg, g.b.deg


def run(l, b, d):
    """dustmaps3d on arrays; NaN distances fall back to each sightline's max_d."""
    from dustmaps3d import dustmaps3d

    d = np.asarray(d, float)
    ebv, dust, sigma, max_d = dustmaps3d(np.asarray(l, float), np.asarray(b, float), d)
    out = pd.DataFrame({
        "E(B-V)_mag": np.asarray(ebv, float),
        "dust_density_mmag_pc": np.asarray(dust, float),
        "sigma_mag": np.asarray(sigma, float),
        "max_distance_kpc": np.asarray(max_d, float),
    })
    out["extrapolated"] = np.nan_to_num(d, nan=-np.inf) > out["max_distance_kpc"].to_numpy()
    return out


def read_table(path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    from astropy.table import Table

    return Table.read(path, format="fits").to_pandas()


def write_table(df, path):
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
        return
    from astropy.table import Table

    # FITS column names cannot contain parentheses
    Table.from_pandas(df.rename(columns={"E(B-V)_mag": "E_B_V_mag"})).write(path, format="fits", overwrite=True)


def query_catalogue(src, dst):
    df = read_table(src)
    cols = {c.lower().strip(): c for c in df.columns}
    if "d" not in cols:
        sys.exit("The table needs a distance column 'd' (kpc; blank = maximum reliable distance).")
    d = pd.to_numeric(df[cols["d"]], errors="coerce").to_numpy(float)
    if np.any(d <= 0):
        sys.exit("Distances must be > 0 kpc (or blank).")
    if "l" in cols and "b" in cols:
        l, b = df[cols["l"]].to_numpy(float), df[cols["b"]].to_numpy(float)
    elif "ra" in cols and "dec" in cols:
        l, b = to_galactic(df[cols["ra"]], df[cols["dec"]])
        df["l"], df["b"] = l, b
    else:
        sys.exit("The table needs columns l,b,d (Galactic) or ra,dec,d (equatorial, ICRS).")
    if np.isnan(l).any() or np.isnan(b).any():
        sys.exit("Coordinates must not be blank.")
    res = run(l, b, d)
    out = pd.concat([df.reset_index(drop=True), res], axis=1)
    write_table(out, dst)
    n_ex = int(res["extrapolated"].sum())
    print(f"wrote {len(out)} rows to {dst}" + (f"; {n_ex} rows have d > max_distance (extrapolated)" if n_ex else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--l", type=float)
    ap.add_argument("--b", type=float)
    ap.add_argument("--ra", type=float)
    ap.add_argument("--dec", type=float)
    ap.add_argument("--d", type=float, help="distance in kpc; omit for the maximum reliable distance")
    ap.add_argument("--input", type=Path, help="CSV or FITS catalogue")
    ap.add_argument("--output", type=Path, help="output CSV or FITS (default: <input>_dustmaps3d.<ext>)")
    args = ap.parse_args()

    if args.input:
        dst = args.output or args.input.with_name(f"{args.input.stem}_dustmaps3d{args.input.suffix}")
        query_catalogue(args.input, dst)
        return
    if args.l is not None and args.b is not None:
        l, b = args.l % 360, args.b
    elif args.ra is not None and args.dec is not None:
        (l,), (b,) = to_galactic([args.ra], [args.dec])
    else:
        ap.error("give --l/--b, --ra/--dec or --input")
    if not -90 <= b <= 90:
        ap.error("latitude must be within [-90, 90]")
    if args.d is not None and args.d <= 0:
        ap.error("--d must be > 0 kpc")
    row = run([l], [b], [np.nan if args.d is None else args.d]).iloc[0]
    print(json.dumps({
        "l_deg": round(float(l), 6), "b_deg": round(float(b), 6),
        "d_kpc": args.d if args.d is not None else float(row["max_distance_kpc"]),
        "E(B-V)_mag": float(row["E(B-V)_mag"]), "sigma_mag": float(row["sigma_mag"]),
        "dust_density_mag_per_kpc": float(row["dust_density_mmag_pc"]),
        "max_distance_kpc": float(row["max_distance_kpc"]), "extrapolated": bool(row["extrapolated"]),
    }, indent=2))


if __name__ == "__main__":
    main()
