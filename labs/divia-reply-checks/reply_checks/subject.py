"""What a reply is checked against: the patient's message, their medicines and, in evals, the expected tag."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from .interfaces import Medicine


class CheckSubject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    message: str
    medicines: tuple[Medicine, ...]
    expected: str | None = None   # the workbook's expected tag; None outside evals (the coach service)
    also: str | None = None
