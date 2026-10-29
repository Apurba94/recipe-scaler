# recipe-scaler

**Scale any buffer or medium recipe to the volume you need, with excess for losses, or plan
a solution from stock solutions (how much of each stock, how much water).**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Lab recipes are written for one batch size ("per 1 L") but you need 350 mL today, or 10% extra for
a plate. Scaling every component by hand, in mixed units, invites mistakes. Writing recipes as simple
text files also gives the lab a shared, versionable recipe collection.

## Features

- Plain-text recipes: `NaCl 8.77 g`, `HCl (1 M) 4 mL`, `water to 1 L` (or `total: 1 L`), `#` comments
- Scale to any target volume with optional excess (`--extra 0.1`), human-friendly units in the output
- Stock planning: for each component give final and stock concentration (M/mM/uM, %, X, mg/mL);
  computes stock volumes (C1V1 = C2V2) and the remaining water, with sanity checks

## Usage

```bash
pip install .
recipe-scaler scale examples/tbs.txt "250 mL"
recipe-scaler scale lb_medium.txt "2 L" --extra 0.05
recipe-scaler stocks '[["Tris pH 8", "20 mM", "1 M"], ["NaCl", "150 mM", "5 M"], ["Tween-20", "0.1 %", "10 %"]]' "500 mL"
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
