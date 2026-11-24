"""Parse the coach's replies: the tag line of one reply, and import files of replies pasted from manual runs.

Import file format (plain text, UTF-8):

    # model: claude-project-manual        optional header lines, before the first block
    # build: CORE-1.0 + XX-1.0
    === F01 run 1 ===
    <the reply exactly as shown, tag line last>
    === F01 run 2 ===
    ...

Reply text is untrusted data: it is only measured and matched, never executed or logged.
"""
from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

MAX_FILE_CHARS = 1_000_000
MAX_REPLY_CHARS = 4096          # a WhatsApp text message is at most 4096 characters
RUNS = (1, 2, 3)

_HEADER = re.compile(r"^=== (\S+) run (\d+) ===$")
_TAG_TOKEN = re.compile(r"\[([A-Z][A-Z ]*)\]")
_META = re.compile(r"^#\s*(model|build):\s*(.+?)\s*$", re.IGNORECASE)


class Tag(StrEnum):
    OK = "OK"
    ESCALATE = "ESCALATE"
    URGENT = "URGENT"


class Reply(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    case_id: str
    run: int
    raw: str
    body: str                  # reply without its tag line; \r\n folded, trailing spaces stripped
    tag: Tag | None
    tag_problem: str | None    # "missing", "invalid: [X]", "more than one tag", "not on last line"


class ImportHeader(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    model: str | None = None
    build: str | None = None


class ImportFileError(ValueError):
    pass


def _normalise(raw: str) -> list[str]:
    lines = [line.rstrip() for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def parse_reply(case_id: str, run: int, raw: str) -> Reply:
    lines = _normalise(raw)
    known = [t for t in _TAG_TOKEN.findall("\n".join(lines)) if t in Tag.__members__]
    last = lines[-1].strip() if lines else ""
    last_token = re.fullmatch(r"\[([A-Z][A-Z ]*)\]", last)
    body_lines = lines[:-1] if last_token else lines
    tag: Tag | None = None
    problem: str | None = None
    if last_token and last_token.group(1) not in Tag.__members__:
        problem = f"invalid: {last}"
    elif len(known) > 1:
        problem = "more than one tag"
    elif last_token:
        tag = Tag(last_token.group(1))
    elif known:
        problem = "not on last line"
    else:
        problem = "missing"
    return Reply(case_id=case_id, run=run, raw=raw, body="\n".join(body_lines).strip("\n"), tag=tag, tag_problem=problem)


def parse_import_file(text: str, known_ids: set[str]) -> tuple[dict[tuple[str, int], Reply], ImportHeader]:
    """Replies keyed by (case ID, run). Any malformed block raises ImportFileError naming its line."""
    if len(text) > MAX_FILE_CHARS:
        raise ImportFileError(f"import file too large ({len(text)} characters; the limit is {MAX_FILE_CHARS})")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    meta: dict[str, str] = {}
    replies: dict[tuple[str, int], Reply] = {}
    current: tuple[str, int, int] | None = None   # case ID, run, header line number
    body: list[str] = []

    def finish() -> None:
        if current is None:
            return
        case_id, run, at = current
        raw = "\n".join(body)
        if not raw.strip():
            raise ImportFileError(f"line {at}: empty reply for {case_id} run {run}")
        if len(raw.strip()) > MAX_REPLY_CHARS:
            raise ImportFileError(f"line {at}: reply for {case_id} run {run} is longer than {MAX_REPLY_CHARS} characters")
        replies[(case_id, run)] = parse_reply(case_id, run, raw)

    for number, line in enumerate(lines, start=1):
        header = _HEADER.match(line.strip())
        if header:
            finish()
            case_id, run = header.group(1), int(header.group(2))
            if run not in RUNS:
                raise ImportFileError(f"line {number}: run {run} for {case_id} is not 1, 2 or 3")
            if case_id not in known_ids:
                raise ImportFileError(f"line {number}: unknown case {case_id}")
            if (case_id, run) in replies:
                raise ImportFileError(f"line {number}: duplicate {case_id} run {run}")
            current, body = (case_id, run, number), []
        elif current is not None:
            body.append(line)
        elif line.strip() and not line.lstrip().startswith("#"):
            raise ImportFileError(f"line {number}: text before the first '=== <ID> run <n> ===' header")
        else:
            m = _META.match(line.strip())
            if m:
                meta[m.group(1).lower()] = m.group(2)
    finish()
    if not replies:
        raise ImportFileError("no replies found: each reply starts with a line like '=== F01 run 1 ==='")
    return replies, ImportHeader(model=meta.get("model"), build=meta.get("build"))
