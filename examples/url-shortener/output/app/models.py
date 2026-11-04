from typing import Any, Literal
from pydantic import BaseModel, Field

Scenario = Literal["greenfield", "brownfield", "ambiguous", "auto"]
Mode = Literal["mock", "remote"]
class RunRequest(BaseModel):
    requirement: str = Field(min_length=8, max_length=12000)
    scenario: Scenario = "auto"
    mode: Mode = "mock"
    repository_context: str = Field(default="", max_length=20000)
class ApprovalRequest(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=2, max_length=120)
    comment: str = Field(default="", max_length=2000)
