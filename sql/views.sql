-- Reporting-Ebene: Sichten, die Tableau und der Monatsbericht direkt nutzen

DROP VIEW IF EXISTS v_plan_ist;
CREATE VIEW v_plan_ist AS
SELECT z.datum, z.jahr, z.monat, z.quartal,
       b.geschaeftsbereich, b.region, k.konto, k.kontotyp,
       SUM(CASE WHEN f.szenario = 'Ist'  THEN f.betrag END) AS ist,
       SUM(CASE WHEN f.szenario = 'Plan' THEN f.betrag END) AS plan
FROM fact_finanzen f
JOIN dim_zeit z    ON z.zeit_id = f.zeit_id
JOIN dim_bereich b ON b.bereich_id = f.bereich_id
JOIN dim_konto k   ON k.konto_id = f.konto_id
GROUP BY z.datum, z.jahr, z.monat, z.quartal, b.geschaeftsbereich, b.region, k.konto, k.kontotyp;

-- GuV-Kennzahlen je Monat und Geschäftsbereich
DROP VIEW IF EXISTS v_kpi_monat;
CREATE VIEW v_kpi_monat AS
SELECT datum, jahr, monat, geschaeftsbereich,
       SUM(CASE WHEN konto = 'Umsatzerlöse' THEN ist END)  AS umsatz_ist,
       SUM(CASE WHEN konto = 'Umsatzerlöse' THEN plan END) AS umsatz_plan,
       SUM(CASE WHEN konto = 'Umsatzerlöse' THEN ist END)
         - SUM(CASE WHEN konto = 'Materialaufwand' THEN ist END)  AS deckungsbeitrag_ist,
       SUM(CASE WHEN konto = 'Umsatzerlöse' THEN plan END)
         - SUM(CASE WHEN konto = 'Materialaufwand' THEN plan END) AS deckungsbeitrag_plan,
       SUM(CASE WHEN kontotyp = 'Erlös' THEN ist ELSE -ist END)   AS ebit_ist,
       SUM(CASE WHEN kontotyp = 'Erlös' THEN plan ELSE -plan END) AS ebit_plan
FROM v_plan_ist
GROUP BY datum, jahr, monat, geschaeftsbereich;
