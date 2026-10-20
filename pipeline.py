"""Datenstrecke: Rohexporte -> Bereinigung & Plausibilisierung -> SQLite-Sternschema
-> Reporting-Sichten -> Tableau-Datei + automatischer Monatsbericht.

Aufruf:  python pipeline.py
"""
import os
import sqlite3
import sys

import pandas as pd

from fpa.etl import clean_actuals, clean_plan
from fpa.report import add_forecast, monthly_report

RAW_IST = "data/raw/erp_ist_export.csv"
RAW_PLAN = "data/raw/planung_export.csv"
DB = "output/finanzen.db"


def load_star_schema(con, ist: pd.DataFrame, plan: pd.DataFrame):
    con.executescript(open("sql/schema.sql", encoding="utf-8").read())
    facts = pd.concat([ist.assign(szenario="Ist"), plan.assign(szenario="Plan")], ignore_index=True)

    zeit = facts[["jahr", "monat"]].drop_duplicates().sort_values(["jahr", "monat"])
    zeit["zeit_id"] = zeit["jahr"] * 100 + zeit["monat"]
    zeit["quartal"] = "Q" + ((zeit["monat"] - 1) // 3 + 1).astype(str)
    zeit["datum"] = zeit.apply(lambda r: f"{r.jahr}-{r.monat:02d}-01", axis=1)
    zeit[["zeit_id", "jahr", "monat", "quartal", "datum"]].to_sql("dim_zeit", con, if_exists="append", index=False)

    bereich = facts[["geschaeftsbereich", "region"]].drop_duplicates().sort_values(["geschaeftsbereich", "region"]).reset_index(drop=True)
    bereich["bereich_id"] = bereich.index + 1
    bereich.to_sql("dim_bereich", con, if_exists="append", index=False)

    konto = facts[["konto", "kontotyp"]].drop_duplicates().sort_values("konto").reset_index(drop=True)
    konto["konto_id"] = konto.index + 1
    konto.to_sql("dim_konto", con, if_exists="append", index=False)

    f = (facts.assign(zeit_id=facts["jahr"] * 100 + facts["monat"])
              .merge(bereich, on=["geschaeftsbereich", "region"])
              .merge(konto, on=["konto", "kontotyp"]))
    f[["zeit_id", "bereich_id", "konto_id", "szenario", "betrag"]].to_sql("fact_finanzen", con, if_exists="append", index=False)
    con.executescript(open("sql/views.sql", encoding="utf-8").read())


def run():
    os.makedirs("output", exist_ok=True)
    raw_ist = pd.read_csv(RAW_IST, sep=";", dtype=str, keep_default_na=False)
    raw_plan = pd.read_csv(RAW_PLAN, sep=";", dtype=str)

    ist, rejected = clean_actuals(raw_ist)
    plan = clean_plan(raw_plan)
    rejected.to_csv("output/abgelehnte_zeilen.csv", index=False, sep=";")

    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    load_star_schema(con, ist, plan)
    plan_ist = pd.read_sql("SELECT * FROM v_plan_ist", con)
    con.close()

    # Abstimmung: Summe in der Datenbank = Summe der bereinigten Daten
    if abs(plan_ist["ist"].sum() - ist["betrag"].sum()) > 0.01:
        sys.exit("Abstimmung fehlgeschlagen: Ist-Summen weichen ab")

    data = add_forecast(plan_ist)
    data["abweichung"] = data["ist"] - data["plan"]
    data.round(2).to_csv("output/tableau_finanzen.csv", index=False, encoding="utf-8")

    last = ist.sort_values(["jahr", "monat"]).iloc[-1]
    year, month = int(last["jahr"]), int(last["monat"])
    report = monthly_report(data, year, month)
    path = f"output/monatsbericht_{year}-{month:02d}.md"
    open(path, "w", encoding="utf-8").write(report)

    print(f"Ist-Zeilen gelesen:   {len(raw_ist)}")
    print(f"Ist-Zeilen geladen:   {len(ist)}")
    print(f"Ist-Zeilen abgelehnt: {len(rejected)}  ->  output/abgelehnte_zeilen.csv")
    for _, r in rejected.iterrows():
        print(f"  Zeile {r.zeile}: {r.grund}")
    print(f"Datenbank:            {DB} (Sternschema + Sichten)")
    print("Tableau-Datei:        output/tableau_finanzen.csv")
    print(f"Monatsbericht:        {path}")


if __name__ == "__main__":
    run()
