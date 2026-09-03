"""Stable API contracts shared by the FastAPI boundary and clients."""

from pydantic import BaseModel, Field


class IntentRequest(BaseModel):
    intent: str = Field(min_length=1, max_length=4000)
    execution_mode: str = Field(default="shadow", pattern="^(shadow|analyze)$")
