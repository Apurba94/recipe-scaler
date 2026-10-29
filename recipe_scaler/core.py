"""Recipes as plain text lines ('Tris base 12.11 g'), scaled by volume, with stock-solution planning."""
import re

MASS = {"kg": 1e3, "g": 1.0, "mg": 1e-3, "ug": 1e-6, "µg": 1e-6}
VOL = {"L": 1.0, "l": 1.0, "mL": 1e-3, "ml": 1e-3, "uL": 1e-6, "µL": 1e-6, "ul": 1e-6}
CONC = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "µM": 1e-6, "%": None, "X": None, "x": None, "mg/mL": None, "g/L": None}
_LINE = re.compile(r"^\s*(?P<name>.+?)\s+(?P<amount>\d*\.?\d+)\s*(?P<unit>[A-Za-zµ%/]+)\s*$")
_TOTAL = re.compile(r"^\s*(?:total|final volume|volume|make up to|fill to)\s*[:=]?\s*(?P<amount>\d*\.?\d+)\s*(?P<unit>[A-Za-zµ]+)\s*$", re.I)
_TOPUP = re.compile(r"(?i)\b(?:to|q\.?s\.?|ad)\b")


def parse_recipe(text):
    """Return (components, total_volume_L, solvent). Components: dicts name, amount (base unit), dim ('mass'/'volume'), unit.

    Lines like 'water to 1 L' or 'total: 500 mL' set the batch volume; '#' starts a comment."""
    comps, total, solvent = [], None, None
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        m = _TOTAL.match(line)
        if m:
            total = float(m.group("amount")) * VOL[m.group("unit")]
            continue
        parts = _TOPUP.split(line)
        if len(parts) == 2 and re.match(r"^\s*\d*\.?\d+\s*[A-Za-zµ]+\s*$", parts[1]):
            amt = re.match(r"^\s*(\d*\.?\d+)\s*([A-Za-zµ]+)", parts[1])
            if amt.group(2) in VOL:
                total = float(amt.group(1)) * VOL[amt.group(2)]
                solvent = parts[0].strip()
                continue
        m = _LINE.match(line)
        if not m:
            raise ValueError("cannot parse recipe line: %r" % raw)
        unit = m.group("unit")
        v = float(m.group("amount"))
        if unit in MASS:
            comps.append({"name": m.group("name"), "amount": v * MASS[unit], "dim": "mass", "unit": unit})
        elif unit in VOL:
            comps.append({"name": m.group("name"), "amount": v * VOL[unit], "dim": "volume", "unit": unit})
        else:
            raise ValueError("unsupported unit %r in line %r" % (unit, raw))
    if total is None:
        raise ValueError("recipe needs a total volume line (e.g. 'water to 1 L' or 'total: 1 L')")
    return comps, total, solvent


def format_amount(value, dim):
    table = [("kg", 1e3), ("g", 1.0), ("mg", 1e-3), ("ug", 1e-6)] if dim == "mass" else [("L", 1.0), ("mL", 1e-3), ("uL", 1e-6)]
    for unit, f in table:
        if abs(value) >= f or unit == table[-1][0]:
            return "%.4g %s" % (value / f, unit)


def scale_recipe(components, total, target, extra=0.0):
    """Scale components from batch volume `total` to `target` (liters), plus an optional excess fraction
    (e.g. 0.1 = 10% extra for pipetting losses)."""
    f = target * (1 + extra) / total
    return [dict(c, scaled=c["amount"] * f) for c in components], target * (1 + extra)


def _conc(text):
    m = re.match(r"^\s*(\d*\.?\d+)\s*([A-Za-zµ%/]+)\s*$", text)
    if not m or m.group(2) not in CONC:
        raise ValueError("bad concentration %r" % text)
    v, u = float(m.group(1)), m.group(2)
    if CONC[u] is not None:
        return v * CONC[u], "molar"
    return v, {"%": "percent", "X": "fold", "x": "fold", "mg/mL": "massconc", "g/L": "massconc"}[u]


def from_stocks(spec, volume):
    """Plan a solution from stock solutions. spec: list of (name, final_conc, stock_conc) strings.

    Returns (rows, water_volume) where rows contain the stock volume to add (C1V1 = C2V2)."""
    rows, used = [], 0.0
    for name, final, stock in spec:
        cf, kf = _conc(final)
        cs, ks = _conc(stock)
        if kf != ks:
            raise ValueError("%s: final and stock concentrations use different kinds of units" % name)
        if cf > cs:
            raise ValueError("%s: final concentration exceeds the stock" % name)
        v = cf * volume / cs
        used += v
        rows.append({"name": name, "final": final, "stock": stock, "volume": v})
    if used > volume:
        raise ValueError("stocks alone exceed the final volume; use more concentrated stocks")
    return rows, volume - used
