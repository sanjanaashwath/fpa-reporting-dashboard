"""Kennzahlen, Hochrechnung und automatischer Monatsbericht."""
import pandas as pd

MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
             "August", "September", "Oktober", "November", "Dezember"]


def eur(x):
    s = f"{x:,.0f}"
    return s.replace(",", ".") + " €"


def pct(x):
    return f"{x:+.1f} %".replace(".", ",")


def add_forecast(plan_ist: pd.DataFrame) -> pd.DataFrame:
    """Hochrechnung: Ist für abgeschlossene Monate, danach Plan × (Ist YTD / Plan YTD)."""
    df = plan_ist.copy()
    keys = ["jahr", "geschaeftsbereich", "region", "konto"]
    closed = df[df["ist"].notna()]
    ytd = closed.groupby(keys)[["ist", "plan"]].sum()
    factor = (ytd["ist"] / ytd["plan"]).rename("faktor").reset_index()
    df = df.merge(factor, on=keys, how="left")
    df["hochrechnung"] = df["ist"].where(df["ist"].notna(), df["plan"] * df["faktor"])
    return df.drop(columns="faktor")


def signed(df, col):
    return df[col].where(df["kontotyp"] == "Erlös", -df[col])


def kpis(df: pd.DataFrame) -> dict:
    """Umsatz, Deckungsbeitrag (Umsatz - Material) und EBIT für Ist, Plan, Hochrechnung."""
    out = {}
    for col in [c for c in ("ist", "plan", "hochrechnung") if c in df.columns]:
        rev = df.loc[df["konto"] == "Umsatzerlöse", col].sum()
        mat = df.loc[df["konto"] == "Materialaufwand", col].sum()
        out[col] = {"umsatz": rev, "deckungsbeitrag": rev - mat, "ebit": signed(df, col).sum()}
    return out


def monthly_report(df: pd.DataFrame, year: int, month: int) -> str:
    ytd = df[(df["jahr"] == year) & (df["monat"] <= month)]
    full = df[df["jahr"] == year]
    k = kpis(ytd)
    fy = kpis(full)
    lines = [f"# Monatsbericht {MONTHS_DE[month - 1]} {year}", "",
             "*Automatisch erzeugt aus `pipeline.py`. Alle Daten sind fiktiv.*", "",
             f"## Kumuliert Januar bis {MONTHS_DE[month - 1]} {year} (YTD)", "",
             "| Kennzahl | Ist | Plan | Abweichung | in % |", "|---|---:|---:|---:|---:|"]
    for name, key in [("Umsatz", "umsatz"), ("Deckungsbeitrag", "deckungsbeitrag"), ("EBIT", "ebit")]:
        i, p = k["ist"][key], k["plan"][key]
        lines.append(f"| {name} | {eur(i)} | {eur(p)} | {eur(i - p)} | {pct((i - p) / abs(p) * 100)} |")

    lines += ["", "## EBIT nach Geschäftsbereich (YTD)", "",
              "| Geschäftsbereich | Ist | Plan | Abweichung | in % |", "|---|---:|---:|---:|---:|"]
    for unit, g in ytd.groupby("geschaeftsbereich"):
        i, p = signed(g, "ist").sum(), signed(g, "plan").sum()
        lines.append(f"| {unit} | {eur(i)} | {eur(p)} | {eur(i - p)} | {pct((i - p) / abs(p) * 100)} |")

    # größte Abweichungen auf Ebene Bereich × Region × Konto (EBIT-Wirkung)
    g = ytd.assign(wirkung=signed(ytd, "ist") - signed(ytd, "plan"))
    top = (g.groupby(["geschaeftsbereich", "region", "konto"])["wirkung"].sum()
             .sort_values(key=abs, ascending=False).head(3))
    lines += ["", "## Größte Abweichungen (Wirkung auf das EBIT, YTD)", ""]
    for (unit, region, konto), v in top.items():
        lines.append(f"- **{unit} / {region} / {konto}:** {eur(v)}")

    i, p = fy["hochrechnung"]["ebit"], fy["plan"]["ebit"]
    lines += ["", f"## Hochrechnung Gesamtjahr {year}", "",
              f"EBIT Hochrechnung: **{eur(i)}** gegenüber Plan {eur(p)} ({pct((i - p) / abs(p) * 100)}).", "",
              "*Hinweis: Die Hochrechnung schreibt die bisherige Ist/Plan-Quote je Bereich, Region und Konto "
              "fort. Sie ist eine Annahme, kein gesicherter Wert.*", ""]
    return "\n".join(lines)
