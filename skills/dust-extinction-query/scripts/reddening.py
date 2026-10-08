"""Reddening coefficients for an E(B-V): Zhang et al. (2024) XP curve or Zhang et al. (2023) empirical.

    python reddening.py --band GAIA3.G --ebv 0.3 --teff 5500
    python reddening.py --color GAIA3.Gbp-GAIA3.Grp --ebv 0.3 --teff 5500
    python reddening.py --model 2023 --band G --ebv 0.3 --teff 5500 --from-3d-map
    python reddening.py --list [--model 2023]

2024 (`pip install xp-extinction-toolkit==1.0`, scipy<1.14) gives A_λ or E(a-b) in mag; R = value / E(B-V).
2023 (`pip install extinction-coefficient==1.8`) gives R; A_λ or E(a-b) = R * E(B-V). The 2023
coefficients are built on SFD: --from-3d-map multiplies an E(B-V) taken from the Wang et al. (2025)
3D map by 1/0.834 first (Wang et al. 2025, Fig. 17). Valid for E(B-V) 0-0.5 mag, Teff 4000-10000 K.
"""
import argparse
import json
import warnings

BANDS_2024 = ["Johnson.U", "Johnson.B", "Johnson.V", "Johnson.R", "GAIA3.Gbp", "GAIA3.G", "GAIA3.Grp",
              "SDSS.u", "SDSS.g", "SDSS.r", "SDSS.i", "SDSS.z", "PS1.g", "PS1.r", "PS1.i", "PS1.z", "PS1.y",
              "2MASS.J", "2MASS.H", "2MASS.Ks", "WISE.W1", "WISE.W2", "WISE.W3", "WISE.W4",
              "GALEX.FUV", "GALEX.NUV", "440", "550"]
BANDS_2023 = ["FUV", "NUV", "g", "r", "i", "z", "y", "u'", "g'", "r'", "i'", "z'", "BP", "G", "RP",
              "J", "H", "Ks", "W1", "W2", "W3", "W4"]
SFD_FACTOR = 1 / 0.834


def xp(identifier, mode, ebv, teff):
    from xp_extinction_toolkit import ExtinctionToolkit

    tool = ExtinctionToolkit()
    e4455 = tool.Cal_E4455(ebv=ebv, Teff=teff)
    calc = tool.star_ext if mode == "ext" else tool.star_reddening
    return float(calc([identifier], E4455=e4455, Teff=[teff])[identifier][0])


def empirical(identifier, ebv, teff):
    from extinction_coefficient import extinction_coefficient

    return float(extinction_coefficient(identifier, EBV=ebv, Teff=teff))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", choices=["2024", "2023"], default="2024")
    ap.add_argument("--band", help="extinction correction for one band")
    ap.add_argument("--color", help="reddening correction for a colour a-b")
    ap.add_argument("--ebv", type=float, default=0.3, help="E(B-V) in mag (default 0.3)")
    ap.add_argument("--teff", type=float, default=5500, help="effective temperature in K (default 5500)")
    ap.add_argument("--from-3d-map", action="store_true", help="2023 only: E(B-V) is from the 3D map, scale by 1/0.834")
    ap.add_argument("--list", action="store_true", help="list band names of the chosen model")
    args = ap.parse_args()

    bands = BANDS_2024 if args.model == "2024" else BANDS_2023
    if args.list:
        print("\n".join(bands))
        return
    if bool(args.band) == bool(args.color):
        ap.error("give exactly one of --band or --color")
    if args.ebv < 0 or args.teff < 1000:
        ap.error("need E(B-V) >= 0 and Teff >= 1000 K")
    mode = "ext" if args.band else "reddening"
    identifier = args.band or args.color
    if any(p not in bands for p in identifier.split("-")):
        ap.error(f"unknown band for the {args.model} model; see --list")

    warnings.filterwarnings("ignore")
    ebv = args.ebv * SFD_FACTOR if (args.model == "2023" and args.from_3d_map) else args.ebv
    if args.model == "2024":
        value = xp(identifier, mode, ebv, args.teff)
        R = value / ebv if ebv > 0 else None
    else:
        R = empirical(identifier, ebv, args.teff)
        value = R * ebv
    key = "A_mag" if mode == "ext" else "E_color_mag"
    print(json.dumps({"model": f"Zhang et al. ({args.model})", "identifier": identifier, "ebv_used": ebv,
                      "teff": args.teff, "R": R, key: value}, indent=2))


if __name__ == "__main__":
    main()
