# Anleitung: Tableau-Dashboard bauen (Tableau Public, kostenlos)

Datei: `output/tableau_finanzen.csv`

## 1. Daten verbinden
1. Öffne **public.tableau.com**, melde dich an und klicke **Erstellen → Web Authoring** (oder nutze Tableau Public Desktop).
2. Lade `tableau_finanzen.csv` hoch.
3. Prüfe die Datentypen: `datum` muss **Datum** sein, `ist`, `plan`, `hochrechnung` und `abweichung` müssen **Zahl** sein.

## 2. Berechnete Felder anlegen
Rechtsklick in den Datenbereich → **Berechnetes Feld erstellen**:

| Name | Formel |
|---|---|
| EBIT Ist | `SUM(IF [kontotyp] = "Erlös" THEN [ist] ELSE -[ist] END)` |
| EBIT Plan | `SUM(IF [kontotyp] = "Erlös" THEN [plan] ELSE -[plan] END)` |
| EBIT Hochrechnung | `SUM(IF [kontotyp] = "Erlös" THEN [hochrechnung] ELSE -[hochrechnung] END)` |
| Umsatz Ist | `SUM(IF [konto] = "Umsatzerlöse" THEN [ist] END)` |
| Umsatz Plan | `SUM(IF [konto] = "Umsatzerlöse" THEN [plan] END)` |
| Deckungsbeitrag Ist | `[Umsatz Ist] - SUM(IF [konto] = "Materialaufwand" THEN [ist] END)` |
| Deckungsbeitrag Plan | `[Umsatz Plan] - SUM(IF [konto] = "Materialaufwand" THEN [plan] END)` |
| EBIT Abweichung | `[EBIT Ist] - [EBIT Plan]` |
| EBIT Abweichung % | `([EBIT Ist] - [EBIT Plan]) / ABS([EBIT Plan])` (Format: Prozent) |
| YTD | `[datum] <= #2025-09-01#` |

## 3. Arbeitsblätter
1. **KPI-Kacheln:** Filter `jahr` = 2025 und `YTD` = Wahr. Ziehe `Umsatz Ist`, `Deckungsbeitrag Ist`, `EBIT Ist` und `EBIT Abweichung %` als Text auf die Markierungen.
2. **Plan-Ist-Verlauf:** `datum` (Monat, stetig) auf Spalten, `EBIT Ist`, `EBIT Plan` und `EBIT Hochrechnung` als Kennzahlen auf Zeilen (Kennzahlwerte), Liniendiagramm. Plan als gestrichelte Linie.
3. **Abweichungen nach Bereich und Region:** `geschaeftsbereich` auf Zeilen, `region` auf Spalten, `EBIT Abweichung` auf Farbe (rot–grün divergierend) und als Text. Diese Heatmap zeigt sofort **Service/Süd** und **Industrie**.
4. **Abweichung nach Konto:** `konto` auf Zeilen, `SUM([abweichung])` auf Spalten, Balkendiagramm.

## 4. Dashboard
1. Neues Dashboard (Größe: Automatisch). Ordne die Kacheln oben an, den Verlauf in der Mitte und darunter die Heatmap und die Konten nebeneinander.
2. Filter für `jahr` und `geschaeftsbereich` auf **alle Arbeitsblätter** anwenden.
3. Heatmap als Filteraktion einstellen: Klick auf eine Zelle filtert die anderen Blätter.
4. Titel: „FP&A Plan-Ist-Analyse 2025“. Füge eine Textbox mit 2 Sätzen Interpretation hinzu (siehe README).

## 5. Veröffentlichen
**Speichern → In Tableau Public veröffentlichen**, den Link kopieren und im README (`LINK-EINFÜGEN`) und im Lebenslauf eintragen.
