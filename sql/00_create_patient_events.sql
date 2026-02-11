/*
  create_patient_events.sql erzeugt eine einheitliche Ereignistabelle aus den
  MIMIC-IV-Modulen hsop, icu und ed als materialized view.
  
  Pro Ereignis wird für jeden Patienten 
  - die Startzeit
  - die Endzeit
  - der Ereignistype aus {hosp, icu, ed}
  - weitere optionale Attribute
  ermittelt.
  
  Wenn die Endzeit NULL ist, wird die Startzeit gesetzt.
*/
CREATE SCHEMA IF NOT EXISTS mimiciv_derived;

DROP MATERIALIZED VIEW IF EXISTS mimiciv_derived.mv_patient_events;

CREATE MATERIALIZED VIEW mimiciv_derived.mv_patient_events AS
WITH hosp AS (
  SELECT
    subject_id,
    admittime::timestamp AS starttime,
    dischtime::timestamp AS endtime,
    'hosp'::text AS event_type,
    hadm_id,
    NULL::bigint AS stay_id,
    'mimiciv_hosp.admissions'::text AS source_table
  FROM mimiciv_hosp.admissions
  WHERE admittime IS NOT NULL
),
icu AS (
  SELECT
    subject_id,
    intime::timestamp AS starttime,
    outtime::timestamp AS endtime,
    'icu'::text AS event_type,
    hadm_id,
    stay_id,
    'mimiciv_icu.icustays'::text AS source_table
  FROM mimiciv_icu.icustays
  WHERE intime IS NOT NULL
),
ed AS (
  SELECT
    subject_id,
    intime::timestamp AS starttime,
    outtime::timestamp AS endtime,
    'ed'::text AS event_type,
    hadm_id,
    stay_id,
    'mimiciv_ed.edstays'::text AS source_table
  FROM mimiciv_ed.edstays
  WHERE intime IS NOT NULL
),
u AS (
  SELECT * FROM hosp
  UNION ALL
  SELECT * FROM icu
  UNION ALL
  SELECT * FROM ed
)
SELECT
  subject_id,
  starttime,
  COALESCE(endtime, starttime) AS endtime,
  event_type,
  hadm_id,
  stay_id,
  source_table
FROM u;

-- Performance: Indizes auf der MV
CREATE INDEX IF NOT EXISTS ix_mv_patient_events_subject
  ON mimiciv_derived.mv_patient_events(subject_id);

CREATE INDEX IF NOT EXISTS ix_mv_patient_events_subject_start_end
  ON mimiciv_derived.mv_patient_events(subject_id, starttime, endtime);
