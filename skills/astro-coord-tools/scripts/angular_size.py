"""Angular diameter <-> physical diameter at a given distance (exact, not small-angle).

    θ = 2·atan(D / 2d)        D = 2·d·tan(θ / 2)

    python angular_size.py size-to-angle --size 10 --size-unit pc --distance 0.4 --distance-unit kpc
    python angular_size.py angle-to-size --angle 8 --angle-unit deg --distance 400 --distance-unit pc

Length units: pc, kpc, Mpc, ly, au, km. Angle units: deg, arcmin, arcsec, mas, rad.
Same formulas and constants as the website's 04 tool.
"""
import argparse
import json
import math

PC = {"pc": 1.0, "kpc": 1e3, "Mpc": 1e6, "ly": 1 / 3.261563777, "au": 1 / 206264.806247, "km": 1 / 3.0856775814913673e13}
ANGLE = {"deg": math.pi / 180, "arcmin": math.pi / 180 / 60, "arcsec": math.pi / 180 / 3600,
         "mas": math.pi / 180 / 3.6e6, "rad": 1.0}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["size-to-angle", "angle-to-size"])
    ap.add_argument("--size", type=float)
    ap.add_argument("--size-unit", choices=list(PC), default="pc")
    ap.add_argument("--angle", type=float)
    ap.add_argument("--angle-unit", choices=list(ANGLE), default="deg")
    ap.add_argument("--distance", type=float, required=True)
    ap.add_argument("--distance-unit", choices=list(PC), default="kpc")
    a = ap.parse_args()

    d = a.distance * PC[a.distance_unit]
    if d <= 0:
        ap.error("distance must be > 0")
    if a.mode == "size-to-angle":
        if a.size is None or a.size <= 0:
            ap.error("give --size > 0")
        th = 2 * math.atan(a.size * PC[a.size_unit] / (2 * d))
        out = {"deg": math.degrees(th), "arcmin": math.degrees(th) * 60, "arcsec": math.degrees(th) * 3600, "rad": th}
    else:
        if a.angle is None or a.angle <= 0:
            ap.error("give --angle > 0")
        th = a.angle * ANGLE[a.angle_unit]
        if th >= math.pi:
            ap.error("angle must be below 180°")
        D = 2 * d * math.tan(th / 2)
        out = {"pc": D, "kpc": D / 1e3, "ly": D * 3.261563777, "au": D * 206264.806247}
    print(json.dumps({"mode": a.mode, "distance_pc": d, "result": out}, indent=2))


if __name__ == "__main__":
    main()
