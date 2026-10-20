import os
import sqlite3
import subprocess
import sys
import unittest

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fpa.etl import clean_actuals, parse_de_number, parse_period  # noqa: E402
from fpa.report import add_forecast, kpis  # noqa: E402


def raw(rows):
    return pd.DataFrame(rows, columns=["Periode", "Geschäftsbereich", "Region", "Konto", "Betrag EUR"])


class TestParsing(unittest.TestCase):
    def test_german_numbers(self):
        self.assertEqual(parse_de_number("1.234,56"), 1234.56)
        self.assertEqual(parse_de_number("12,5"), 12.5)
        self.assertEqual(parse_de_number("1.000.000,00"), 1_000_000.0)
        self.assertIsNone(parse_de_number("n/a"))
        self.assertIsNone(parse_de_number(""))

    def test_period(self):
        self.assertEqual(parse_period("03.2025"), (2025, 3))
        self.assertIsNone(parse_period("13.2025"))
        self.assertIsNone(parse_period("2025-03"))


class TestCleaning(unittest.TestCase):
    def test_spellings_are_unified(self):
        df, rej = clean_actuals(raw([
            ["01.2025", "INDUSTRIE", "Süd", " Umsatzerlöse ", "100,00"],
            ["01.2025", "Industrie", "Süd", "Sonst. betr. Aufwendungen", "10,00"],
        ]))
        self.assertEqual(len(rej), 0)
        self.assertEqual(set(df["geschaeftsbereich"]), {"Industrie"})
        self.assertIn("Sonstige betriebliche Aufwendungen", set(df["konto"]))

    def test_invalid_rows_are_rejected_with_reason(self):
        df, rej = clean_actuals(raw([
            ["01.2025", "Handel", "Nord", "Umsatzerlöse", "100,00"],
            ["01.2025", "Handel", "Nord", "Umsatzerlöse", "100,00"],   # Dublette
            ["13.2025", "Handel", "Nord", "Umsatzerlöse", "100,00"],   # Periode
            ["01.2025", "Logistik", "Nord", "Umsatzerlöse", "100,00"], # Bereich
            ["01.2025", "Handel", "Nord", "Zinsertrag", "100,00"],     # Konto
            ["01.2025", "Handel", "Nord", "Umsatzerlöse", "-5,00"],    # negativ
        ]))
        self.assertEqual(len(df), 1)
        self.assertEqual(len(rej), 5)
        self.assertTrue(rej["grund"].str.len().gt(0).all())


class TestKpis(unittest.TestCase):
    def setUp(self):
        rows = []
        for m in (1, 2, 3):
            ist = None if m == 3 else 1
            rows += [
                {"jahr": 2025, "monat": m, "geschaeftsbereich": "Handel", "region": "Nord",
                 "konto": "Umsatzerlöse", "kontotyp": "Erlös", "plan": 100.0, "ist": None if ist is None else 110.0},
                {"jahr": 2025, "monat": m, "geschaeftsbereich": "Handel", "region": "Nord",
                 "konto": "Materialaufwand", "kontotyp": "Aufwand", "plan": 50.0, "ist": None if ist is None else 50.0},
            ]
        self.df = pd.DataFrame(rows)

    def test_deckungsbeitrag_and_ebit(self):
        k = kpis(self.df[self.df["monat"] <= 2])
        self.assertAlmostEqual(k["ist"]["umsatz"], 220)
        self.assertAlmostEqual(k["ist"]["deckungsbeitrag"], 120)
        self.assertAlmostEqual(k["plan"]["ebit"], 100)

    def test_forecast_uses_run_rate(self):
        f = add_forecast(self.df)
        open_month = f[(f["monat"] == 3) & (f["konto"] == "Umsatzerlöse")]
        self.assertAlmostEqual(open_month["hochrechnung"].iloc[0], 110.0)  # Plan 100 x Quote 1,1


class TestPipeline(unittest.TestCase):
    """Ende-zu-Ende: Pipeline läuft und Datenbank stimmt mit den Rohdaten überein."""

    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "generate_data.py"], cwd=ROOT, check=True, capture_output=True)
        subprocess.run([sys.executable, "pipeline.py"], cwd=ROOT, check=True, capture_output=True)

    def test_outputs_exist(self):
        for f in ("finanzen.db", "tableau_finanzen.csv", "abgelehnte_zeilen.csv", "monatsbericht_2025-09.md"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, "output", f)), f)

    def test_star_schema_has_no_orphans(self):
        con = sqlite3.connect(os.path.join(ROOT, "output", "finanzen.db"))
        orphans = con.execute("""SELECT COUNT(*) FROM fact_finanzen f
                                 LEFT JOIN dim_konto k ON k.konto_id = f.konto_id
                                 WHERE k.konto_id IS NULL""").fetchone()[0]
        plan_rows = con.execute("SELECT COUNT(*) FROM fact_finanzen WHERE szenario='Plan'").fetchone()[0]
        con.close()
        self.assertEqual(orphans, 0)
        self.assertEqual(plan_rows, 2 * 12 * 3 * 4 * 4)  # Jahre x Monate x Bereiche x Regionen x Konten

    def test_six_rows_rejected(self):
        rej = pd.read_csv(os.path.join(ROOT, "output", "abgelehnte_zeilen.csv"), sep=";")
        self.assertEqual(len(rej), 6)


if __name__ == "__main__":
    unittest.main()
