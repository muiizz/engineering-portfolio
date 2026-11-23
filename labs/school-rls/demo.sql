BEGIN;
CREATE ROLE demo_east NOLOGIN;
CREATE ROLE demo_west NOLOGIN;
CREATE ROLE demo_head_office NOLOGIN;
CREATE ROLE demo_teacher NOLOGIN;
CREATE SCHEMA school_demo;
CREATE TABLE school_demo.applicants (
  id integer PRIMARY KEY,
  campus name NOT NULL,
  stage text NOT NULL CHECK (stage IN ('review','admitted'))
);
INSERT INTO school_demo.applicants VALUES (1,'demo_east','review'), (2,'demo_west','review');
ALTER TABLE school_demo.applicants ENABLE ROW LEVEL SECURITY;
CREATE POLICY campus_read ON school_demo.applicants FOR SELECT
  USING (campus = current_user);
CREATE POLICY head_office_read ON school_demo.applicants FOR SELECT TO demo_head_office USING (true);
GRANT USAGE ON SCHEMA school_demo TO demo_east, demo_west, demo_head_office, demo_teacher;
GRANT SELECT ON school_demo.applicants TO demo_head_office, demo_teacher;
CREATE TABLE school_demo.admission_audit (
  applicant_id integer PRIMARY KEY REFERENCES school_demo.applicants(id),
  actor name NOT NULL,
  admitted_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
GRANT SELECT ON school_demo.admission_audit TO demo_head_office;
GRANT SELECT ON school_demo.applicants TO demo_east, demo_west;

CREATE FUNCTION school_demo.admit(applicant integer) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $$
DECLARE caller name := current_setting('role');
BEGIN
  UPDATE school_demo.applicants SET stage = 'admitted'
  WHERE id = applicant AND (campus = caller OR caller = 'demo_head_office') AND stage = 'review';
  IF NOT FOUND THEN RETURN false; END IF;
  INSERT INTO school_demo.admission_audit (applicant_id, actor) VALUES (applicant, caller);
  RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION school_demo.admit(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION school_demo.admit(integer) TO demo_east, demo_west, demo_head_office;

SET ROLE demo_east;
DO $$
BEGIN
  IF (SELECT array_agg(id) FROM school_demo.applicants) IS DISTINCT FROM ARRAY[1]
    THEN RAISE EXCEPTION 'east scope failed'; END IF;
  IF school_demo.admit(2) THEN RAISE EXCEPTION 'cross-campus admission'; END IF;
  IF NOT school_demo.admit(1) THEN RAISE EXCEPTION 'valid admission rejected'; END IF;
  IF school_demo.admit(1) THEN RAISE EXCEPTION 'duplicate admission'; END IF;
  IF has_table_privilege(current_user,'school_demo.applicants','UPDATE')
    THEN RAISE EXCEPTION 'direct update granted'; END IF;
END;
$$;
SET ROLE demo_west;
DO $$
BEGIN
  IF (SELECT array_agg(id) FROM school_demo.applicants) IS DISTINCT FROM ARRAY[2]
    THEN RAISE EXCEPTION 'west scope failed'; END IF;
  IF NOT school_demo.admit(2) THEN RAISE EXCEPTION 'valid west admission rejected'; END IF;
END;
$$;
SET ROLE demo_teacher;
DO $$
BEGIN
  IF EXISTS (SELECT FROM school_demo.applicants)
    THEN RAISE EXCEPTION 'teacher read applicants'; END IF;
  IF has_function_privilege(current_user,'school_demo.admit(integer)','EXECUTE')
    THEN RAISE EXCEPTION 'teacher can admit'; END IF;
END;
$$;
RESET ROLE;
INSERT INTO school_demo.applicants VALUES (3,'demo_west','review');
SET ROLE demo_head_office;
DO $$
BEGIN
  IF (SELECT count(*) FROM school_demo.applicants) <> 3
    THEN RAISE EXCEPTION 'head office scope failed'; END IF;
  IF NOT school_demo.admit(3) THEN RAISE EXCEPTION 'head office admission failed'; END IF;
  IF (SELECT array_agg(actor::text ORDER BY applicant_id) FROM school_demo.admission_audit)
    IS DISTINCT FROM ARRAY['demo_east','demo_west','demo_head_office']
    THEN RAISE EXCEPTION 'audit actor or row count mismatch'; END IF;
  IF has_table_privilege(current_user,'school_demo.admission_audit','UPDATE')
    OR has_table_privilege(current_user,'school_demo.admission_audit','DELETE')
    OR has_table_privilege(current_user,'school_demo.admission_audit','INSERT')
    THEN RAISE EXCEPTION 'audit write granted'; END IF;
END;
$$;
RESET ROLE;

CREATE TABLE school_demo.sections (
  id integer PRIMARY KEY, school_year integer NOT NULL, grade integer NOT NULL,
  display_name text NOT NULL, sort_order integer NOT NULL CHECK (sort_order > 0),
  UNIQUE (school_year, grade, sort_order)
);
INSERT INTO school_demo.sections VALUES
  (10,2025,5,'Maple',1),(11,2025,5,'Oak',2),
  (20,2026,6,'Oak',1),(21,2026,6,'Cedar',2);
DO $$
DECLARE target integer;
BEGIN
  SELECT next.id INTO target FROM school_demo.sections AS prior
  JOIN school_demo.sections AS next ON next.school_year = prior.school_year + 1
    AND next.grade = prior.grade + 1 AND next.sort_order = prior.sort_order
  WHERE prior.id = 11;
  IF target IS DISTINCT FROM 21 THEN RAISE EXCEPTION 'wrong destination'; END IF;
END;
$$;
SELECT 'PASS: campus visibility, guarded transitions, and position-based promotion';
ROLLBACK;
