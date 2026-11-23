-- Apply to a disposable Supabase database as its migration owner.
CREATE SCHEMA school_reference;
CREATE TABLE school_reference.memberships (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id),
  role text NOT NULL CHECK (role IN ('head_office','principal','teacher','accountant','parent')),
  campus text,
  CHECK (role <> 'principal' OR campus IS NOT NULL)
);
CREATE TABLE school_reference.applicants (
  id integer PRIMARY KEY,
  campus text NOT NULL,
  stage text NOT NULL DEFAULT 'review' CHECK (stage IN ('review','admitted'))
);
CREATE TABLE school_reference.audit (
  applicant_id integer PRIMARY KEY REFERENCES school_reference.applicants(id),
  actor uuid NOT NULL,
  previous_stage text NOT NULL,
  new_stage text NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE school_reference.memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_reference.applicants ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_reference.audit ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON SCHEMA school_reference FROM PUBLIC;
GRANT USAGE ON SCHEMA school_reference TO authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA school_reference FROM PUBLIC, anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA school_reference TO authenticated;

CREATE POLICY own_membership ON school_reference.memberships
  FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));
CREATE POLICY applicant_visibility ON school_reference.applicants
  FOR SELECT TO authenticated USING (EXISTS (
    SELECT 1 FROM school_reference.memberships m
    WHERE m.user_id = (SELECT auth.uid())
      AND (m.role = 'head_office' OR (m.role = 'principal' AND m.campus = applicants.campus))
  ));
CREATE POLICY audit_visibility ON school_reference.audit
  FOR SELECT TO authenticated USING (EXISTS (
    SELECT 1 FROM school_reference.memberships m
    WHERE m.user_id = (SELECT auth.uid()) AND m.role = 'head_office'
  ));

CREATE FUNCTION public.school_reference_admit(applicant integer) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $$
DECLARE actor_id uuid := auth.uid();
BEGIN
  UPDATE school_reference.applicants a SET stage = 'admitted'
  WHERE a.id = applicant AND a.stage = 'review'
    AND EXISTS (
      SELECT 1 FROM school_reference.memberships m WHERE m.user_id = actor_id
        AND (m.role = 'head_office' OR (m.role = 'principal' AND m.campus = a.campus))
    );
  IF NOT FOUND THEN RETURN false; END IF;
  INSERT INTO school_reference.audit (applicant_id,actor,previous_stage,new_stage)
    VALUES (applicant,actor_id,'review','admitted');
  RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION public.school_reference_admit(integer) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.school_reference_admit(integer) TO authenticated;
