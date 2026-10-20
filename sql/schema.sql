-- Sternschema für das Finanz-Reporting
DROP TABLE IF EXISTS fact_finanzen;
DROP TABLE IF EXISTS dim_zeit;
DROP TABLE IF EXISTS dim_bereich;
DROP TABLE IF EXISTS dim_konto;

CREATE TABLE dim_zeit (
    zeit_id   INTEGER PRIMARY KEY,   -- JJJJMM
    jahr      INTEGER NOT NULL,
    monat     INTEGER NOT NULL,
    quartal   TEXT    NOT NULL,
    datum     TEXT    NOT NULL       -- erster Tag des Monats, für Tableau
);
CREATE TABLE dim_bereich (
    bereich_id        INTEGER PRIMARY KEY,
    geschaeftsbereich TEXT NOT NULL,
    region            TEXT NOT NULL,
    UNIQUE (geschaeftsbereich, region)
);
CREATE TABLE dim_konto (
    konto_id  INTEGER PRIMARY KEY,
    konto     TEXT NOT NULL UNIQUE,
    kontotyp  TEXT NOT NULL CHECK (kontotyp IN ('Erlös', 'Aufwand'))
);
CREATE TABLE fact_finanzen (
    zeit_id    INTEGER NOT NULL REFERENCES dim_zeit(zeit_id),
    bereich_id INTEGER NOT NULL REFERENCES dim_bereich(bereich_id),
    konto_id   INTEGER NOT NULL REFERENCES dim_konto(konto_id),
    szenario   TEXT    NOT NULL CHECK (szenario IN ('Ist', 'Plan')),
    betrag     REAL    NOT NULL,
    PRIMARY KEY (zeit_id, bereich_id, konto_id, szenario)
);
