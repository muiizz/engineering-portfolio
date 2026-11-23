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
