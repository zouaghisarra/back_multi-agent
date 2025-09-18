from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# ===== SCHÉMAS DE SORTIE STRUCTURÉE =====

class ClarifyWithUser(BaseModel):
    need_clarification: bool
    question: str
    verification: str

class ResearchQuestion(BaseModel):
    research_brief: str

# ===== ÉTAT DU SCOPE =====

class ScopeState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    research_brief: str
    country: str
    research_topic: str 
    official_domains: list[str]