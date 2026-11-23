-- Run as the migration owner after applying supabase.sql in a disposable database.
BEGIN;
INSERT INTO auth.users (id) SELECT ('00000000-0000-0000-0000-' || lpad(i::text,12,'0'))::uuid
FROM generate_series(1,7) AS g(i);
INSERT INTO school_reference.memberships VALUES
 ('00000000-0000-0000-0000-000000000001','principal','east'),
 ('00000000-0000-0000-0000-000000000002','principal','west'),
 ('00000000-0000-0000-0000-000000000003','head_office',NULL),
 ('00000000-0000-0000-0000-000000000004','teacher','east'),
 ('00000000-0000-0000-0000-000000000005','accountant','east'),
 ('00000000-0000-0000-0000-000000000006','parent','west');
INSERT INTO school_reference.applicants (id,campus) VALUES (1,'east'),(2,'west'),(3,'west');
DO $$
BEGIN
  IF has_function_privilege('anon','public.school_reference_admit(integer)','EXECUTE')
    OR has_schema_privilege('anon','school_reference','USAGE')
    THEN RAISE EXCEPTION 'anonymous access granted'; END IF;
END;
$$;
SET LOCAL ROLE authenticated;
DO $$
DECLARE n integer;
DECLARE visible integer[];
BEGIN
  FOR n IN 1..7 LOOP
    PERFORM set_config('request.jwt.claim.sub','00000000-0000-0000-0000-' || lpad(n::text,12,'0'),true);
    SELECT coalesce(array_agg(id ORDER BY id),ARRAY[]::integer[])
      INTO visible FROM school_reference.applicants;
    IF visible IS DISTINCT FROM (CASE n WHEN 1 THEN ARRAY[1] WHEN 2 THEN ARRAY[2,3]
        WHEN 3 THEN ARRAY[1,2,3] ELSE ARRAY[]::integer[] END)
      THEN RAISE EXCEPTION 'wrong visibility for fixture %', n; END IF;
    IF (SELECT count(*) FROM school_reference.memberships) <> (CASE WHEN n=7 THEN 0 ELSE 1 END)
      THEN RAISE EXCEPTION 'wrong membership visibility'; END IF;
    IF n<>3 AND EXISTS (SELECT FROM school_reference.audit)
      THEN RAISE EXCEPTION 'audit exposed'; END IF;
    IF n>3 AND public.school_reference_admit(3)
      THEN RAISE EXCEPTION 'unexpected admission for fixture %', n; END IF;
  END LOOP;
  IF has_table_privilege(current_user,'school_reference.memberships','UPDATE')
     OR has_table_privilege(current_user,'school_reference.applicants','UPDATE')
     OR has_table_privilege(current_user,'school_reference.audit','INSERT,UPDATE,DELETE')
    THEN RAISE EXCEPTION 'direct table write granted'; END IF;
  PERFORM set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
  IF public.school_reference_admit(2) THEN RAISE EXCEPTION 'cross-campus admission'; END IF;
  IF NOT public.school_reference_admit(1) THEN RAISE EXCEPTION 'east admission failed'; END IF;
  IF public.school_reference_admit(1) THEN RAISE EXCEPTION 'duplicate admission'; END IF;
  IF EXISTS (SELECT FROM school_reference.audit) THEN RAISE EXCEPTION 'audit exposed'; END IF;
  PERFORM set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',true);
  IF NOT public.school_reference_admit(2) THEN RAISE EXCEPTION 'head office admission failed'; END IF;
  IF (SELECT count(*) FROM school_reference.audit WHERE previous_stage='review' AND new_stage='admitted')<>2
    THEN RAISE EXCEPTION 'wrong audit rows'; END IF;
  IF (SELECT actor FROM school_reference.audit WHERE applicant_id=1)
      IS DISTINCT FROM '00000000-0000-0000-0000-000000000001'::uuid
    THEN RAISE EXCEPTION 'wrong audit actor'; END IF;
END;
$$;
SELECT 'PASS: Supabase identity contract, five roles, anonymous and unlinked access, admission audit';
ROLLBACK;
