# FP&A Reporting: Plan-Ist-Analyse mit SQL, Python und Tableau

**Wie entwickelt sich das Ergebnis gegenüber dem Plan, wo entstehen die Abweichungen, und wo landen wir am Jahresende?**

Dieses Projekt zeigt eine komplette Reporting-Datenstrecke für das Finanzcontrolling (FP&A) eines fiktiven Unternehmens mit drei Geschäftsbereichen und vier Regionen: von unordentlichen Rohexporten bis zum Tableau-Dashboard und einem automatisch erzeugten Monatsbericht.

*English summary: an end-to-end FP&A reporting pipeline (messy ERP and planning exports → validation → SQLite star schema → SQL reporting views → Tableau dashboard and an automated monthly report). All data is synthetic.*

## Datenstrecke

```
ERP-Export (Ist)  ─┐
                   ├─> Bereinigung & Plausibilisierung ─> Sternschema (SQLite) ─> SQL-Sichten ─┬─> Tableau-Dashboard
Planungs-Export  ──┘     (fpa/etl.py)                     (sql/schema.sql)        (sql/views.sql)└─> Monatsbericht (Markdown)
```

| Schritt | Was passiert | Warum es wichtig ist |
|---|---|---|
| 1. Bereinigung | Deutsche Zahlenformate (`1.234,56`), uneinheitliche Schreibweisen (`INDUSTRIE`, `Sonst. betr. Aufwendungen`), Plan vom Breit- ins Langformat | Ist und Plan werden überhaupt erst vergleichbar |
| 2. Plausibilisierung | Ungültige Perioden, unbekannte Bereiche/Konten, fehlende Beträge und Dubletten werden **nicht still gelöscht**, sondern mit Grund in `output/abgelehnte_zeilen.csv` gemeldet | Nachvollziehbar, welche Daten fehlen und mit dem Fachbereich geklärt werden müssen |
| 3. Datenmodell | Sternschema mit `fact_finanzen` und den Dimensionen Zeit, Bereich, Konto | Ein Modell für Ist und Plan, erweiterbar um weitere Szenarien |
| 4. Abstimmung | Summe in der Datenbank = Summe der bereinigten Ist-Daten, sonst bricht die Pipeline ab | Vertrauen in die Zahlen |
| 5. Reporting-Ebene | SQL-Sichten `v_plan_ist` und `v_kpi_monat` (Umsatz, Deckungsbeitrag, EBIT) | Tableau und Bericht nutzen dieselbe Logik |
| 6. Hochrechnung | Ist für abgeschlossene Monate, danach Plan × bisherige Ist/Plan-Quote | Erwartetes Jahresergebnis, klar als Annahme gekennzeichnet |
| 7. Automatischer Monatsbericht | `output/monatsbericht_2025-09.md` mit YTD-Kennzahlen, größten Abweichungen und Hochrechnung | Kein manuelles Zusammenkopieren mehr |

## Ergebnis (September 2025, YTD)

| Kennzahl | Ist | Plan | Abweichung |
|---|---:|---:|---:|
| Umsatz | 8,34 Mio. € | 8,33 Mio. € | +0,0 % |
| Deckungsbeitrag | 4,35 Mio. € | 4,48 Mio. € | −2,9 % |
| EBIT | 1,49 Mio. € | 1,63 Mio. € | −8,5 % |

**Interpretation:** Der Umsatz liegt im Plan, das EBIT aber 8,5 % darunter. Die Ursachen sind zwei klar abgrenzbare Effekte:
1. **Industrie:** höherer Materialaufwand ab April 2025 (Preissteigerung) drückt den Deckungsbeitrag.
2. **Service, Region Süd:** Umsatzrückgang ab Juni 2025 (Verlust eines Großkunden).

Das Umsatzplus im **Handel Ost** gleicht den Umsatz aus, verbessert das Ergebnis aber kaum, weil der Materialaufwand mitwächst. Die Hochrechnung erwartet für 2025 ein EBIT von 2,07 Mio. € statt 2,26 Mio. € (−8,5 %).

**Empfehlung:** Preisanpassung oder Einkaufsverhandlungen in der Industrie prüfen und für Service Süd einen Plan zur Neukundengewinnung aufsetzen.

## Tableau-Dashboard

Das Dashboard basiert auf `output/tableau_finanzen.csv`: KPI-Kacheln, Plan-Ist-Verlauf mit Hochrechnung, Abweichungen nach Bereich und Region.
➡️ **[Dashboard auf Tableau Public](LINK-EINFÜGEN)**. Die Anleitung zum Nachbauen steht in [TABLEAU_ANLEITUNG.md](TABLEAU_ANLEITUNG.md).

## Ausführen

```bash
pip install -r requirements.txt
python generate_data.py   # erzeugt fiktive Rohdaten in data/raw/
python pipeline.py        # Bereinigung, Datenbank, Tableau-Datei, Monatsbericht
python -m unittest -v     # 9 Tests
```

## Dateien

- `fpa/etl.py`: Bereinigung und Plausibilisierung
- `fpa/report.py`: Kennzahlen, Hochrechnung, Monatsbericht
- `sql/schema.sql`, `sql/views.sql`: Sternschema und Reporting-Sichten
- `pipeline.py`: die komplette Datenstrecke
- `tests/`: Unit- und Ende-zu-Ende-Tests

*Alle Daten sind fiktiv und werden von `generate_data.py` erzeugt.*

Autorin: Sanjana Aswathaiah
