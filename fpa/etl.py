"""Extract, Transform, Validate: macht aus Rohexporten saubere, plausibilisierte Tabellen."""
import re

import pandas as pd

UNITS = {"industrie": "Industrie", "handel": "Handel", "service": "Service"}
REGIONS = {"nord": "Nord", "süd": "Süd", "sued": "Süd", "west": "West", "ost": "Ost"}
ACCOUNTS = {
    "umsatzerlöse": ("Umsatzerlöse", "Erlös"),
    "materialaufwand": ("Materialaufwand", "Aufwand"),
    "personalaufwand": ("Personalaufwand", "Aufwand"),
    "sonstige betriebliche aufwendungen": ("Sonstige betriebliche Aufwendungen", "Aufwand"),
    "sonst. betr. aufwendungen": ("Sonstige betriebliche Aufwendungen", "Aufwand"),
}


def parse_de_number(text):
    """'1.234,56' -> 1234.56; None, wenn kein gültiger Betrag."""
    if text is None:
        return None
    s = str(text).strip().replace("€", "").replace(" ", "")
    if not re.fullmatch(r"-?[\d.]+(,\d+)?", s):
        return None
    return float(s.replace(".", "").replace(",", "."))


def parse_period(text):
    """'03.2025' -> (2025, 3); None bei ungültiger Periode."""
    m = re.fullmatch(r"\s*(\d{1,2})\.(\d{4})\s*", str(text))
    if not m:
        return None
    month, year = int(m.group(1)), int(m.group(2))
    if not 1 <= month <= 12:
        return None
    return year, month


def _norm(text, mapping):
    return mapping.get(str(text).strip().lower())


def clean_actuals(raw: pd.DataFrame):
    """Gibt (saubere Ist-Daten, abgelehnte Zeilen mit Grund) zurück."""
    clean, rejected = [], []
    seen = set()
    for i, row in raw.iterrows():
        line = i + 2  # Zeile in der CSV-Datei (Header = 1)
        period = parse_period(row["Periode"])
        unit = _norm(row["Geschäftsbereich"], UNITS)
        region = _norm(row["Region"], REGIONS)
        acc = _norm(row["Konto"], ACCOUNTS)
        amount = parse_de_number(row["Betrag EUR"])
        reason = None
        if period is None:
            reason = f"ungültige Periode '{row['Periode']}'"
        elif unit is None:
            reason = f"unbekannter Geschäftsbereich '{row['Geschäftsbereich']}'"
        elif region is None:
            reason = f"unbekannte Region '{row['Region']}'"
        elif acc is None:
            reason = f"unbekanntes Konto '{row['Konto']}'"
        elif amount is None:
            reason = f"kein gültiger Betrag '{row['Betrag EUR']}'"
        elif amount < 0:
            reason = "negativer Betrag (Storno prüfen)"
        if reason:
            rejected.append({"zeile": line, "grund": reason})
            continue
        key = (period, unit, region, acc[0], round(amount, 2))
        if key in seen:
            rejected.append({"zeile": line, "grund": "Dublette"})
            continue
        seen.add(key)
        clean.append({"jahr": period[0], "monat": period[1], "geschaeftsbereich": unit,
                      "region": region, "konto": acc[0], "kontotyp": acc[1], "betrag": amount})
    return pd.DataFrame(clean), pd.DataFrame(rejected, columns=["zeile", "grund"])


def clean_plan(raw: pd.DataFrame) -> pd.DataFrame:
    """Planung vom breiten Format (M01..M12) ins lange Format bringen."""
    long = raw.melt(id_vars=["Jahr", "Geschäftsbereich", "Region", "Konto"],
                    var_name="m", value_name="wert")
    out = pd.DataFrame({
        "jahr": long["Jahr"].astype(int),
        "monat": long["m"].str[1:].astype(int),
        "geschaeftsbereich": long["Geschäftsbereich"].map(lambda t: _norm(t, UNITS)),
        "region": long["Region"].map(lambda t: _norm(t, REGIONS)),
        "konto": long["Konto"].map(lambda t: _norm(t, ACCOUNTS)[0]),
        "kontotyp": long["Konto"].map(lambda t: _norm(t, ACCOUNTS)[1]),
        "betrag": long["wert"].map(parse_de_number),
    })
    if out.isna().any().any():
        raise ValueError("Planung enthält ungültige Werte")
    return out
