"""Stand-ins written for this public copy. NOT Divia code.

In Divia these types come from the rules engine, the workbook loader and the content loader, which
stay private. Only the fields the published checks read are kept here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

# Tag severity, lowest first. The rules engine's NONE and ROUTINE both mean the coach replies [OK].
TAG_SEVERITY = {"OK": 1, "ESCALATE": 2, "URGENT": 3}


class Level(StrEnum):
    URGENT = "URGENT"
    ESCALATE = "ESCALATE"
    ROUTINE = "ROUTINE"
    NONE = "NONE"


def level_to_tag(level: Level) -> str:
    return "OK" if level in (Level.NONE, Level.ROUTINE) else level.value


class Medicine(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    name: str = Field(min_length=1, max_length=80)


class RulesResult(BaseModel):
    """What the rules engine decided about one message: a level, and which approved messages apply."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    level: Level
    message_keys: tuple[str, ...] = ()
    approved_message_missing: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContentPack:
    approved: dict[str, dict[str, str]]                      # message key -> {language label -> approved text}
    required_steps: dict[str, dict[str, tuple[str, ...]]]    # message key -> {language label -> steps, in order}
    hindi_words: tuple[str, ...] = ()
    banned_phrases: tuple[str, ...] = ()


class EvalCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    message: str
    expected: str
    also: str | None = None
    medicines: tuple[Medicine, ...] = ()
    runs_not_needed: frozenset[int] = frozenset()

    @property
    def subject(self):  # type: ignore[no-untyped-def]
        from .subject import CheckSubject  # imported here: subject.py imports this module
        return CheckSubject(message=self.message, medicines=self.medicines, expected=self.expected, also=self.also)
