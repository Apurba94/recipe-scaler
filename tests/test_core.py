import io
import os
import unittest
from contextlib import redirect_stdout

from recipe_scaler.cli import main
from recipe_scaler.core import format_amount, from_stocks, parse_recipe, scale_recipe

EX = os.path.join(os.path.dirname(__file__), "..", "examples", "tbs.txt")
with open(EX, encoding="utf-8") as fh:
    TBS = fh.read()


class RecipeTests(unittest.TestCase):
    def test_parse(self):
        comps, total, solvent = parse_recipe(TBS)
        self.assertEqual([c["name"] for c in comps], ["Tris base", "NaCl", "HCl (1 M)"])
        self.assertEqual((total, solvent), (1.0, "water"))
        self.assertAlmostEqual(comps[2]["amount"], 0.004)

    def test_total_line_variants_and_errors(self):
        self.assertEqual(parse_recipe("NaCl 1 g\ntotal: 500 mL")[1], 0.5)
        with self.assertRaises(ValueError):
            parse_recipe("NaCl 1 g")
        with self.assertRaises(ValueError):
            parse_recipe("NaCl 1 parsec\ntotal: 1 L")

    def test_scale(self):
        comps, total, _ = parse_recipe(TBS)
        rows, final = scale_recipe(comps, total, 0.25)
        self.assertAlmostEqual(rows[0]["scaled"], 1.515)
        rows, final = scale_recipe(comps, total, 0.25, extra=0.1)
        self.assertAlmostEqual(final, 0.275)
        self.assertEqual(format_amount(rows[1]["scaled"], "mass"), "2.412 g")
        self.assertEqual(format_amount(0.0011, "volume"), "1.1 mL")

    def test_from_stocks(self):
        rows, water = from_stocks([("Tris", "20 mM", "1 M"), ("NaCl", "150 mM", "5 M"), ("Tween", "0.1 %", "10 %")], 0.5)
        self.assertAlmostEqual(rows[0]["volume"], 0.01)
        self.assertAlmostEqual(rows[1]["volume"], 0.015)
        self.assertAlmostEqual(rows[2]["volume"], 0.005)
        self.assertAlmostEqual(water, 0.47)
        with self.assertRaises(ValueError):
            from_stocks([("x", "2 M", "1 M")], 1)
        with self.assertRaises(ValueError):
            from_stocks([("x", "1 mM", "1 %")], 1)

    def test_cli(self):
        with redirect_stdout(io.StringIO()) as buf:
            main(["scale", EX, "250 mL"])
            main(["stocks", '[["Tris", "20 mM", "1 M"]]', "100 mL"])
        out = buf.getvalue()
        self.assertIn("Tris base                      1.515 g", out)
        self.assertIn("add 2 mL", out)


if __name__ == "__main__":
    unittest.main()
