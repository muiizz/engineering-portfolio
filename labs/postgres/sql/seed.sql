CREATE TABLE attendance (
    attendance_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id integer NOT NULL,
    student_id integer NOT NULL,
    attended_on date NOT NULL,
    present boolean NOT NULL
);

INSERT INTO attendance (tenant_id, student_id, attended_on, present)
SELECT
    1 + i % 100,
    1 + (i / 100) % 1000,
    DATE '2024-01-01' + ((i * 131::bigint + (i / 100) * 17) % 730)::integer,
    (i * 13::bigint + i / 100) % 20 <> 0
FROM generate_series(0, 999999) AS series(i);

VACUUM (ANALYZE) attendance;
