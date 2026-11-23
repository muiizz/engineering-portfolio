"""Exercise real Supabase Auth and the PostgREST admission endpoint."""
import json
import os
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID

base = os.environ["API_URL"]
anon = os.environ["ANON_KEY"]
service = os.environ["SERVICE_ROLE_KEY"]
db = os.environ["DB_URL"]


def post(path, body, api_key=anon, token=None):
    request = Request(
        base + path, json.dumps(body).encode(),
        {"Content-Type": "application/json", "apikey": api_key,
         "Authorization": "Bearer " + (token or api_key)},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def create_session(email):
    password = "Synthetic-local-test-only-4!"
    status, user = post("/auth/v1/admin/users", {
        "email": email, "password": password, "email_confirm": True,
    }, service)
    assert status in (200, 201), status
    status, session = post("/auth/v1/token?grant_type=password", {
        "email": email, "password": password,
    })
    assert status == 200, status
    return UUID(user["id"]), session["access_token"]


def sql(query):
    return subprocess.check_output(
        ["psql", "-XAt", "-v", "ON_ERROR_STOP=1", db, "-c", query], text=True,
    ).strip()


principal, principal_token = create_session("principal@example.test")
_, unlinked_token = create_session("unlinked@example.test")
sql(f"""
INSERT INTO school_reference.memberships VALUES ('{principal}', 'principal', 'east');
INSERT INTO school_reference.applicants (id,campus) VALUES (101,'east'),(102,'west');
NOTIFY pgrst, 'reload schema';
""")
endpoint = "/rest/v1/rpc/school_reference_admit"
assert post(endpoint, {"applicant": 101}, token=unlinked_token) == (200, False)
assert post(endpoint, {"applicant": 102}, token=principal_token) == (200, False)
assert post(endpoint, {"applicant": 101}, token=principal_token) == (200, True)
assert post(endpoint, {"applicant": 101}, token=principal_token) == (200, False)
assert sql("SELECT actor FROM school_reference.audit WHERE applicant_id=101") == str(principal)
assert sql("SELECT count(*) FROM school_reference.audit") == "1"
print("PASS: Auth login, signed JWT, PostgREST admission, audit and cross-campus denial")
