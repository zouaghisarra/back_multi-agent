from pydantic import BaseModel
from typing import Optional
from source.agents.orchestrator.schema import AgentState


class QARequest(AgentState):
    question: str
    max_length: Optional[int] = 400
    temperature: Optional[float] = 0.3
    language:str = "fr"

class QAResponse(BaseModel):
    answer: str
    status: str = "success"