-- Run on a fresh disposable PostgreSQL cluster started with
-- shared_preload_libraries=pg_stat_statements, after loading sql/seed.sql.
\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SET application_name = 'attendance-query-lab';
SELECT format('SELECT count(*) FROM attendance WHERE tenant_id = %s', n)
FROM generate_series(1,5) AS g(n)
\gexec
SELECT format('SELECT count(*) FROM attendance WHERE NOT present AND tenant_id = %s', n)
FROM generate_series(1,3) AS g(n)
\gexec
SELECT calls, round(total_exec_time::numeric,3) AS total_ms,
       shared_blks_hit, shared_blks_read, query
FROM pg_stat_statements
WHERE query LIKE 'SELECT count(*) FROM attendance WHERE%'
ORDER BY total_exec_time DESC;
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_stat_statements
    WHERE query LIKE 'SELECT count(*) FROM attendance WHERE tenant_id = %' AND calls >= 5)
  THEN RAISE EXCEPTION 'expected normalized query statistics'; END IF;
END;
$$;
