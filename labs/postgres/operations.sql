-- Run only after sql/seed.sql on a fresh disposable database.
\set ON_ERROR_STOP on
CREATE ROLE attendance_reader NOLOGIN;
GRANT SELECT ON attendance TO attendance_reader;
CREATE FUNCTION lab_tenant() RETURNS integer
LANGUAGE plpgsql STABLE AS $$
BEGIN
  RETURN current_setting('lab.tenant')::integer;
END;
$$;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_visibility ON attendance TO attendance_reader
USING (tenant_id = lab_tenant());
SET lab.tenant = '37';
SET ROLE attendance_reader;
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM attendance;
RESET ROLE;

ALTER POLICY tenant_visibility ON attendance TO attendance_reader
USING (tenant_id = (SELECT lab_tenant()));
SET ROLE attendance_reader;
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM attendance;
RESET ROLE;
CREATE INDEX CONCURRENTLY attendance_tenant_lab_idx ON attendance(tenant_id);
SET ROLE attendance_reader;
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM attendance;
DO $$
BEGIN
  IF (SELECT count(*) FROM attendance) <> 10000
     OR EXISTS (SELECT FROM attendance WHERE tenant_id <> 37)
  THEN RAISE EXCEPTION 'RLS changed visible results'; END IF;
END;
$$;
RESET ROLE;

-- Adding a constant default and backfilling a different column in chunks.
SET lock_timeout = '2s';
ALTER TABLE attendance ADD COLUMN source text NOT NULL DEFAULT 'fixture';
ALTER TABLE attendance ADD COLUMN reported_present boolean;
SELECT format('UPDATE attendance SET reported_present=present WHERE attendance_id > %s AND attendance_id <= %s',
              n, n + 50000)
FROM generate_series(0,950000,50000) AS g(n)
\gexec
ALTER TABLE attendance ADD CONSTRAINT reported_present_complete
  CHECK (reported_present IS NOT NULL) NOT VALID;
ALTER TABLE attendance VALIDATE CONSTRAINT reported_present_complete;
ALTER TABLE attendance ALTER COLUMN reported_present SET NOT NULL;
DO $$
BEGIN
  IF EXISTS (SELECT FROM attendance WHERE reported_present IS DISTINCT FROM present OR source <> 'fixture')
  THEN RAISE EXCEPTION 'backfill mismatch'; END IF;
END;
$$;

-- Prevent auto-cleanup during this small controlled measurement.
ALTER TABLE attendance SET (autovacuum_enabled = false);
VACUUM (ANALYZE) attendance;
UPDATE attendance SET source = 'reviewed' WHERE attendance_id <= 100000;
SELECT pg_stat_force_next_flush();
SELECT n_live_tup, n_dead_tup, pg_relation_size('attendance') AS heap_bytes
FROM pg_stat_user_tables WHERE relname='attendance';
VACUUM (ANALYZE) attendance;
SELECT n_live_tup, n_dead_tup, pg_relation_size('attendance') AS heap_bytes
FROM pg_stat_user_tables WHERE relname='attendance';
ALTER TABLE attendance RESET (autovacuum_enabled);
