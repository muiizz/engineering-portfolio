"""Flag openings and closings that many replies in one run share. Reported for reviewers; never blocking."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .replies import Reply

_WORD = re.compile(r"\w+")


class RepetitionFlag(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    run: int
    kind: Literal["opening", "closing"]
    phrase: str
    count: int
    total: int
    case_ids: tuple[str, ...]


def ends_of(reply: Reply, words: int) -> tuple[str, str] | None:
    """The first and last `words` words of a reply (casefolded), or None for an empty reply."""
    lines = [line for line in reply.body.splitlines() if line.strip()]
    if not lines:
        return None
    first, last = _WORD.findall(lines[0].casefold()), _WORD.findall(lines[-1].casefold())
    return " ".join(first[:words]), " ".join(last[-words:])


def repetition_flags(replies: list[Reply], max_share: float, min_count: int, words: int) -> list[RepetitionFlag]:
    by_run: dict[int, list[Reply]] = defaultdict(list)
    for reply in replies:
        by_run[reply.run].append(reply)
    flags: list[RepetitionFlag] = []
    for run in sorted(by_run):
        total = len(by_run[run])
        kinds: tuple[tuple[int, Literal["opening", "closing"]], ...] = ((0, "opening"), (1, "closing"))
        for index, kind in kinds:
            groups: dict[str, list[str]] = defaultdict(list)
            for reply in by_run[run]:
                ends = ends_of(reply, words)
                if ends and ends[index]:
                    groups[ends[index]].append(reply.case_id)
            for phrase, ids in sorted(groups.items()):
                if len(ids) >= min_count and len(ids) / total > max_share:
                    flags.append(RepetitionFlag(run=run, kind=kind, phrase=phrase, count=len(ids), total=total,
                                                case_ids=tuple(sorted(ids))))
    return flags
