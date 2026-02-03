\copy (
WITH notes AS (
    SELECT
        subject_id,
        charttime,
        'discharge'::text AS src,
        note_id,
        note_seq,
        text
    FROM mimiciv_note.discharge

    UNION ALL

    SELECT
        subject_id,
        charttime,
        'radiology'::text AS src,
        note_id,
        note_seq,
        text
    FROM mimiciv_note.radiology
),
per_patient AS (
    SELECT
        subject_id,
        string_agg(
            ('[' || to_char(charttime, 'YYYY-MM-DD HH24:MI:SS') || '] '
             || src || E'\n' || text),
            E'\n\n' ORDER BY charttime, src, note_id, note_seq
        ) AS body
    FROM notes
    GROUP BY subject_id
)
SELECT
    ('subject_id=' || subject_id || E'\n' || body || E'\n\n-----\n') AS patient_block
FROM per_patient
ORDER BY subject_id;
) TO 'mimic_notes.txt' WITH (FORMAT text, ENCODING 'UTF8');
