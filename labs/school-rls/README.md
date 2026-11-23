# School access and promotion reference

Run `psql -X -v ON_ERROR_STOP=1 -f demo.sql` as an administrator on an
empty disposable PostgreSQL database. The transaction rolls back schema,
roles, and data. The SQL uses invented campuses and section names.

Two campus staff roles can read their own applicants. Direct table writes
are withheld. A security-definer admission function checks campus and current
state before it updates a row. The test exercises both roles.

The promotion fixture intentionally reuses a section name at a different
position next year. It checks that a student follows the section position
even when the destination has a different name.

This reference models identity with PostgreSQL roles. Supabase deployments
normally map authenticated identities to trusted membership records. 

## Role matrix

| Role | Read applicants | Admit via RPC | Read audit | Modify audit |
|---|---|---|---|---|
| East principal | East | East | No | No |
| West principal | West | West | No | No |
| Head office | All | All | Yes | No |
| Teacher | None | No | No | No |

A successful admission and its audit record commit together. Rejected and
repeated calls create no audit record. Verified with PostgreSQL 16.2.

## Supabase identity and access

In a disposable Supabase database, apply supabase.sql as the migration owner,
then run verify_supabase.sql with psql and ON_ERROR_STOP enabled. For plain
PostgreSQL, apply auth_fixture.sql first to supply the auth.uid contract.
The standalone demo.sql also exercises position-based promotion.

The identity-based matrix includes two campus principals, head office,
teachers, accountants, parents, an unlinked authenticated account, and anon.
Only principals for the matching campus and head office may admit. Teachers,
accountants, parents, and unlinked identities see no applicant rows. Head
office can read the admission audit. Authenticated callers cannot write to
these tables directly.

Verified on PostgreSQL 16.2 using auth_fixture.sql. Full Supabase Auth and
PostgREST were not exercised. The school_reference schema is accessed directly
by SQL for the tests. The public admission function can be called as an RPC.
