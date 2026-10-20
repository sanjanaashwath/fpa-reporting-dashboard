"""Erzeugt fiktive Finanzdaten (Ist aus dem ERP, Plan aus dem Planungstool).

Die Ist-Daten sind bewusst "unordentlich", wie echte Exporte:
deutsche Zahlenformate, Leerzeichen, uneinheitliche Schreibweisen,
doppelte Zeilen und einige fehlerhafte Datensätze.
"""
import csv
import os
import random

import numpy as np

random.seed(7)
rng = np.random.default_rng(7)

UNITS = ["Industrie", "Handel", "Service"]
REGIONS = ["Nord", "Süd", "West", "Ost"]
# Basis-Monatsumsatz je Geschäftsbereich (EUR)
BASE_REVENUE = {"Industrie": 420_000, "Handel": 310_000, "Service": 180_000}
REGION_SHARE = {"Nord": 0.22, "Süd": 0.34, "West": 0.26, "Ost": 0.18}
MATERIAL_RATE = {"Industrie": 0.48, "Handel": 0.62, "Service": 0.15}
PERSONNEL_RATE = {"Industrie": 0.22, "Handel": 0.14, "Service": 0.52}
OTHER_RATE = 0.09
SEASON = [0.86, 0.90, 1.02, 1.00, 1.03, 0.98, 0.92, 0.88, 1.05, 1.10, 1.12, 1.14]

ACT_MONTHS = [(2024, m) for m in range(1, 13)] + [(2025, m) for m in range(1, 10)]
PLAN_MONTHS = [(2024, m) for m in range(1, 13)] + [(2025, m) for m in range(1, 13)]


def plan_values(year, month, unit, region):
    growth = 1.0 if year == 2024 else 1.06
    rev = BASE_REVENUE[unit] * REGION_SHARE[region] * SEASON[month - 1] * growth
    return {
        "Umsatzerlöse": rev,
        "Materialaufwand": rev * MATERIAL_RATE[unit],
        "Personalaufwand": rev * PERSONNEL_RATE[unit],
        "Sonstige betriebliche Aufwendungen": rev * OTHER_RATE,
    }


def actual_values(year, month, unit, region):
    p = plan_values(year, month, unit, region)
    a = {k: v * rng.normal(1.0, 0.035) for k, v in p.items()}
    # Story 1: Materialpreise steigen ab April 2025 (v. a. Industrie)
    if year == 2025 and month >= 4 and unit == "Industrie":
        a["Materialaufwand"] *= 1.09
    # Story 2: Service in Region Süd verliert ab Juni 2025 einen Großkunden
    if year == 2025 and month >= 6 and unit == "Service" and region == "Süd":
        a["Umsatzerlöse"] *= 0.78
    # Story 3: Handel Ost wächst stärker als geplant
    if year == 2025 and unit == "Handel" and region == "Ost":
        a["Umsatzerlöse"] *= 1.08
        a["Materialaufwand"] *= 1.08
    return a


def de_number(x):
    """1234567.891 -> '1.234.567,89' (deutsches Format)."""
    s = f"{x:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def messy_account(name):
    variants = {
        "Umsatzerlöse": ["Umsatzerlöse", "UMSATZERLÖSE", " Umsatzerlöse "],
        "Materialaufwand": ["Materialaufwand", "materialaufwand"],
        "Personalaufwand": ["Personalaufwand", "Personalaufwand "],
        "Sonstige betriebliche Aufwendungen": ["Sonstige betriebliche Aufwendungen", "Sonst. betr. Aufwendungen"],
    }
    return random.choice(variants[name])


def main():
    os.makedirs("data/raw", exist_ok=True)
    rows = []
    for (y, m) in ACT_MONTHS:
        for u in UNITS:
            for r in REGIONS:
                for acc, val in actual_values(y, m, u, r).items():
                    rows.append([f"{m:02d}.{y}", random.choice([u, u, u.upper()]), r, messy_account(acc), de_number(val)])
    # typische Exportfehler
    rows.append(rows[10][:])                                   # Dublette
    rows.append(rows[25][:])                                   # Dublette
    rows.append(["13.2025", "Handel", "Nord", "Umsatzerlöse", "1.000,00"])   # ungültiger Monat
    rows.append(["05.2025", "Logistik", "Nord", "Umsatzerlöse", "5.000,00"]) # unbekannter Bereich
    rows.append(["05.2025", "Handel", "Süd", "Zinsertrag", "2.000,00"])       # unbekanntes Konto
    rows.append(["06.2025", "Industrie", "West", "Umsatzerlöse", "n/a"])      # kein Betrag
    random.shuffle(rows)
    with open("data/raw/erp_ist_export.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Periode", "Geschäftsbereich", "Region", "Konto", "Betrag EUR"])
        w.writerows(rows)

    # Plan: breites Format (ein Monat pro Spalte), wie aus einem Planungstool
    with open("data/raw/planung_export.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Jahr", "Geschäftsbereich", "Region", "Konto"] + [f"M{m:02d}" for m in range(1, 13)])
        for y in (2024, 2025):
            for u in UNITS:
                for r in REGIONS:
                    vals = {m: plan_values(y, m, u, r) for m in range(1, 13)}
                    for acc in vals[1]:
                        w.writerow([y, u, r, acc] + [de_number(vals[m][acc]) for m in range(1, 13)])
    print("Rohdaten erzeugt in data/raw/")


if __name__ == "__main__":
    main()
