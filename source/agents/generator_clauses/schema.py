from pydantic import BaseModel
from typing import Literal
from source.agents.orchestrator.schema import AgentState
class ClauseRequest(AgentState):
    description: str
    language: Literal["fr", "en"] = "fr"
    max_length: int = 300
    temperature: float = 0.7