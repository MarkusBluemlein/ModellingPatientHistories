/*
  create_patient_index.sql ermittelt Stammdaten zu den Patienten: 
  - demografische Daten (gender, anchor_age, anchor_year, anchor_year_group)
  - Todesdatum
  - Erstkontakt als Minimum der Startzeitenn in den Events
  - letzte Entlassung als Maximum der Endzeiten in den Events
  - das globale Ende aller Beobachtunge
  - das Ende der Beobachtungen eines Patienten
  - Kennzeichen ob ein Tod beobachtet wurde
  */
  
DROP MATERIALIZED VIEW IF EXISTS mimiciv_derived.mv_patient_index;

CREATE MATERIALIZED VIEW mimiciv_derived.mv_patient_index AS
WITH agg AS (
  SELECT
    subject_id,
    MIN(starttime) AS first_contact,
    MAX(endtime)   AS last_discharge
  FROM mimiciv_derived.mv_patient_events
  GROUP BY subject_id
),
glob AS (
  SELECT MAX(endtime) AS global_observation_end
  FROM mimiciv_derived.mv_patient_events
)
SELECT
  p.subject_id,
  p.gender,
  p.anchor_age,
  p.anchor_year,
  p.anchor_year_group,
  p.dod,
  a.first_contact,
  a.last_discharge,
  g.global_observation_end,
  LEAST(a.last_discharge + interval '1 year', g.global_observation_end) AS observation_end,
  (p.dod IS NOT NULL AND p.dod <= LEAST(a.last_discharge + interval '1 year', g.global_observation_end))
    AS has_observed_death
FROM mimiciv_hosp.patients p
JOIN agg a ON a.subject_id = p.subject_id
CROSS JOIN glob g;

CREATE INDEX IF NOT EXISTS ix_mv_patient_index_subject
  ON mimiciv_derived.mv_patient_index(subject_id);

CREATE INDEX IF NOT EXISTS ix_mv_patient_index_first_contact
  ON mimiciv_derived.mv_patient_index(first_contact);

CREATE INDEX IF NOT EXISTS ix_mv_patient_index_observation_end
  ON mimiciv_derived.mv_patient_index(observation_end);
