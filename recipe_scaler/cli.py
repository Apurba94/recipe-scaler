"""Command-line interface for recipe-scaler."""
import argparse
import json
import re

from .core import format_amount, from_stocks, parse_recipe, scale_recipe

_V = {"L": 1.0, "mL": 1e-3, "ml": 1e-3, "uL": 1e-6}


def _volume(text):
    m = re.match(r"^\s*(\d*\.?\d+)\s*(L|mL|ml|uL)\s*$", text)
    if not m:
        raise argparse.ArgumentTypeError("volume like '250 mL'")
    return float(m.group(1)) * _V[m.group(2)]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="recipe-scaler", description="Scale lab recipes or plan from stock solutions.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scale")
    s.add_argument("recipe", help="text file, one component per line ('NaCl 8.77 g', 'water to 1 L')")
    s.add_argument("volume", type=_volume, help="target volume, e.g. '250 mL'")
    s.add_argument("--extra", type=float, default=0.0, help="excess fraction, e.g. 0.1 for +10%%")
    st = sub.add_parser("stocks")
    st.add_argument("spec", help="JSON list of [name, final, stock], e.g. [[\"Tris\", \"20 mM\", \"1 M\"]]")
    st.add_argument("volume", type=_volume)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "scale":
            with open(args.recipe, encoding="utf-8") as fh:
                comps, total, solvent = parse_recipe(fh.read())
            rows, final = scale_recipe(comps, total, args.volume, args.extra)
            print("Recipe for %s (batch %s, factor %.4g):" % (format_amount(final, "volume"), format_amount(total, "volume"),
                                                             final / total))
            for r in rows:
                print("  %-30s %s" % (r["name"], format_amount(r["scaled"], r["dim"])))
            print("  %-30s to %s" % (solvent or "solvent", format_amount(final, "volume")))
        else:
            spec = json.loads(args.spec) if args.spec.strip().startswith("[") else json.load(open(args.spec, encoding="utf-8"))
            rows, water = from_stocks(spec, args.volume)
            for r in rows:
                print("  %-20s %-10s from %-10s add %s" % (r["name"], r["final"], r["stock"], format_amount(r["volume"], "volume")))
            print("  %-20s add %s" % ("water", format_amount(water, "volume")))
    except ValueError as exc:
        print("error: %s" % exc)
        return 1
    return 0
